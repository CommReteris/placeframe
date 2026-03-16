using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using Serilog.Core;
using Serilog.Events;
using Serilog.Parsing;
using UnityEngine;

namespace Outernet.Client
{
    public class Enricher : ILogEventEnricher
    {
        public static ScalarValue methodSignatureKey = new ScalarValue("methodSignature");
        public static ScalarValue fileNameKey = new ScalarValue("fileName");
        public static ScalarValue lineNumberKey = new ScalarValue("lineNumber");

        private static Regex anonymousFunctionRegex = new Regex(@"\<(?<method>\w+)\>b__\d+_(?<index>\d+)");
        private static Regex asyncStateMachineRegex = new Regex(@"\<(?<method>\w+)\>d__\d+");

        private static readonly string unityProjectRoot = Path.GetFullPath(Application.dataPath + "/..");

        static readonly Dictionary<LogEventLevel, LogLevel> logLevelMap = new Dictionary<LogEventLevel, LogLevel>
        {
            { LogEventLevel.Verbose, LogLevel.Trace },
            { LogEventLevel.Debug, LogLevel.Debug },
            { LogEventLevel.Information, LogLevel.Info },
            { LogEventLevel.Warning, LogLevel.Warn },
            { LogEventLevel.Error, LogLevel.Error },
            { LogEventLevel.Fatal, LogLevel.Fatal }
        };

        public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
        {
            // If the log event has an exception, enrich with exception details
            if (logEvent.Exception != null)
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("exception", SerilogException(logEvent.Exception)));

                // If the log event is an uncaught exception, we have no more information to add
                // logEvent.Properties.TryGetValue("logGroup", out var logGroup);
                // if ((string)((ScalarValue)logGroup).Value == "UncaughtException") return;
            }

            logEvent.AddPropertyIfAbsent(new LogEventProperty("messageTemplate", new ScalarValue(logEvent.MessageTemplate.Text)));
            logEvent.AddPropertyIfAbsent(new LogEventProperty("message", new ScalarValue(logEvent.MessageTemplate.Render(logEvent.Properties))));
            logEvent.AddPropertyIfAbsent(new LogEventProperty("deviceName", new ScalarValue(Logger.DeviceName)));

            var room = ConnectionManager.RoomConnectionRequested?.Value;
            if (room != null)
            {
                logEvent.AddOrUpdateProperty(propertyFactory.CreateProperty("room", room));
            }

            var propertyTokens = logEvent.MessageTemplate.Tokens
                .OfType<PropertyToken>()
                .Where(token => token.Format != null);

            // If the message template contained formatting tokens, enrich with the rendered properties
            if (propertyTokens.Any())
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("properties", new SequenceValue(propertyTokens.Select(token =>
                {
                    using var stringWriter = new System.IO.StringWriter();
                    token.Render(logEvent.Properties, stringWriter);
                    return new ScalarValue(stringWriter.ToString());
                }))));
            }

            // If the log level is greater than or equal to the configured stack trace level, enrich with the stack trace
            if (logLevelMap[logEvent.Level] >= Log.stackTraceLevel)
            {
                logEvent.AddPropertyIfAbsent(new LogEventProperty("stackTrace", SerilogStackTrace()));
            }
        }

        DictionaryValue SerilogException(Exception exception)
        {
            var properties = new Dictionary<ScalarValue, LogEventPropertyValue>
            {
                { new ScalarValue("type"), new ScalarValue(exception.GetType().FullName) },
                { new ScalarValue("message"), new ScalarValue(exception.Message) }
            };

            if (exception is WebRequestException)
            {
                properties.Add(new ScalarValue("httpStatusCode"), new ScalarValue((exception as WebRequestException).StatusCode));
                properties.Add(new ScalarValue("httpResponse"), new ScalarValue((exception as WebRequestException).Response));
            }

            if (exception.StackTrace != null)
            {
                properties.Add(new ScalarValue("stackTrace"), SerilogStackTrace(exception));
            }

            if (exception is AggregateException aggregateException)
            {
                properties.Add(new ScalarValue("innerExceptions"), new SequenceValue(aggregateException.InnerExceptions.Select(SerilogException)));
            }
            else if (exception.InnerException != null)
            {
                properties.Add(new ScalarValue("innerException"), SerilogException(exception.InnerException));
            }

            if (exception is ResponseDeserializationException)
            {
                properties.Add(new ScalarValue("json"), new ScalarValue((exception as ResponseDeserializationException).Json));
            }

            return new DictionaryValue(properties);
        }

        private static int _diagCount = 0;

        SequenceValue SerilogStackTrace(Exception exception = null)
        {
            bool diag = _diagCount < 3;
            _diagCount++;
            if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", "[EnricherDiag] SerilogStackTrace entry");

            var stackTrace = exception != null
                ? new StackTrace(exception, true)
                : new StackTrace(true);

            if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] stackTrace null? {stackTrace == null}");

            var rawFrames = stackTrace.GetFrames();
            if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] GetFrames() null? {rawFrames == null}, count={rawFrames?.Length}");

            var frames = (rawFrames ?? Array.Empty<StackFrame>()).AsEnumerable();

            if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] unityProjectRoot null? {unityProjectRoot == null}, value={unityProjectRoot}");

            var result = new SequenceValue(frames.Select((frame, index) =>
            {
                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] null? {frame == null}");

                var method = frame.GetMethod();
                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] GetMethod() null? {method == null}");

                if (method == null)
                {
                    return new DictionaryValue(new Dictionary<ScalarValue, LogEventPropertyValue>
                    {
                        { methodSignatureKey, new ScalarValue("<unknown method>") }
                    });
                }

                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] method.Name={method.Name}, DeclaringType null? {method.DeclaringType == null}, DeclaringType={method.DeclaringType}");

                var methodParameters = method.GetParameters();
                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] GetParameters() null? {methodParameters == null}, count={methodParameters?.Length}");

                if (methodParameters != null)
                {
                    for (int i = 0; i < methodParameters.Length; i++)
                    {
                        if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] param[{i}] null? {methodParameters[i] == null}, ParameterType null? {methodParameters[i]?.ParameterType == null}, Name={methodParameters[i]?.ParameterType?.Name}");
                    }
                }

                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] calling BuildMethodName");
                var methodSignature = BuildMethodName(method);
                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] BuildMethodName returned: {methodSignature}");

                methodSignature += methodParameters.Length == 0 ? "()" : $"({string.Join(", ", methodParameters.Select(parameter => parameter.ParameterType.Name))})";
                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] full signature: {methodSignature}");

                var properties = new Dictionary<ScalarValue, LogEventPropertyValue>
                {
                    { methodSignatureKey, new ScalarValue(methodSignature) }
                };

                var fileName = frame.GetFileName();
                if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] frame[{index}] fileName={fileName}");

                if (fileName != null && fileName != string.Empty)
                {
                    fileName = Path.GetFullPath(fileName);
                    if (fileName.StartsWith(unityProjectRoot))
                    {
                        fileName = fileName.Substring(unityProjectRoot.Length + 1);
                    }

                    properties.Add(fileNameKey, new ScalarValue(fileName));
                    properties.Add(lineNumberKey, new ScalarValue(frame.GetFileLineNumber()));
                }

                return new DictionaryValue(properties);
            }));

            if (diag) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] SerilogStackTrace call #{_diagCount} completed OK");
            return result;
        }

        private static string BuildMethodName(MethodBase method)
        {
            if (method == null) return null;

            var methodName = method.Name;
            var type = method.DeclaringType;

            if (_diagCount <= 3) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] BuildMethodName: methodName={methodName}, IsGenericMethod={method.IsGenericMethod}, DeclaringType null? {type == null}, DeclaringType={type}");

            if (method.IsGenericMethod)
            {
                var genericArgs = method.GetGenericArguments();
                if (_diagCount <= 3) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] BuildMethodName: GetGenericArguments() null? {genericArgs == null}, count={genericArgs?.Length}");
                methodName += $"<{string.Join(", ", genericArgs.Select(arg => arg.Name))}>";
            }

            if (type != null)
            {
                var typeName = type.Name;
                if (_diagCount <= 3) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] BuildMethodName: typeName={typeName}, IsNested={type.IsNested}");

                if (typeName.StartsWith("<>c"))
                {
                    if (_diagCount <= 3) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] BuildMethodName: lambda type, type.DeclaringType null? {type.DeclaringType == null}, type.DeclaringType={type.DeclaringType}");
                    var match = anonymousFunctionRegex.Match(methodName);
                    var enclosingMethodName = match.Groups["method"].Value;
                    var lambdaIndex = match.Groups["index"].Value;
                    return $"{BuildTypeName(type.DeclaringType)}.{enclosingMethodName}+[Anonymous_{lambdaIndex}]";
                }

                if (typeName.Contains("d__"))
                {
                    if (_diagCount <= 3) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] BuildMethodName: async SM type, type.DeclaringType null? {type.DeclaringType == null}, type.DeclaringType={type.DeclaringType}");
                    var match = asyncStateMachineRegex.Match(typeName);
                    var originalMethodName = match.Groups["method"].Value;
                    return $"{BuildTypeName(type.DeclaringType)}.{originalMethodName}+[AsyncStateMachine].{methodName}";
                }

                return $"{BuildTypeName(type)}.{methodName}";
            }

            return methodName;
        }

        private static string BuildTypeName(Type type)
        {
            if (_diagCount <= 3) Logger.defaultUnityLogHandler.LogFormat(LogType.Log, null, "{0}", $"[EnricherDiag] BuildTypeName: type null? {type == null}, type={type}");

            string typeName = type.Name;

            // If this is a generic type, append the generic arguments to the type name
            // if (type.IsGenericType)
            // {
            //     // Remove the backtick and the number of generic arguments from the type name
            //     typeName = typeName.Substring(0, typeName.IndexOf('`'));

            //     var genericArgs = type.GetGenericArguments()
            //         .Select(arg =>
            //         {
            //             // If this generic argument is an async state machine, use a less cryptic name
            //             if (arg.Name.Contains("d__"))
            //             {
            //                 var match = asyncStateMachineRegex.Match(arg.Name);
            //                 var methodName = match.Groups["method"].Value;
            //                 return $"{methodName}+[AsyncStateMachine]";
            //             }
            //             return arg.Name;
            //         });

            //     typeName += $"<{string.Join(", ", genericArgs)}>";
            // }

            // If this is a nested type, prepend the declaring type name
            if (type.IsNested)
            {
                return $"{BuildTypeName(type.DeclaringType)}+{typeName}";
            }

            // If this type is in a namespace, prepend the namespace
            if (type.Namespace != null)
            {
                return $"{type.Namespace}.{typeName}";
            }

            return typeName;
        }
    }
}

