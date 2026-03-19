using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Serilog;
using Serilog.Configuration;
using Serilog.Core;
using Serilog.Events;
using UnityEngine;

namespace Outernet.Client
{
    static class UnityLoggerConfiguration
    {
        public static LoggerConfiguration Unity(this LoggerSinkConfiguration loggerConfiguration)
        {
            return loggerConfiguration.Sink(new UnityDebugSink());
        }

        class UnityDebugSink : ILogEventSink
        {
            static readonly Dictionary<LogEventLevel, LogType> logLevelMap = new Dictionary<LogEventLevel, LogType>
            {
                { LogEventLevel.Verbose, LogType.Log },
                { LogEventLevel.Debug, LogType.Log },
                { LogEventLevel.Information, LogType.Log },
                { LogEventLevel.Warning, LogType.Warning },
                { LogEventLevel.Error, LogType.Error },
                { LogEventLevel.Fatal, LogType.Error }
            };

            public void Emit(LogEvent logEvent)
            {
                string logGroup = (string)(logEvent.Properties.GetValueOrDefault("logGroup") as ScalarValue).Value;
                string prelude = Log.ColorPalette.ContainsKey(logGroup) ?
                    $"<color={Log.ColorPalette[logGroup]}>[{logGroup}]</color>" :
                    $"[{logGroup}]";

                string message;

                if (logEvent.Properties.TryGetValue("message", out var messageProperty))
                {
                    message = $"{prelude} {(string)(messageProperty as ScalarValue).Value}";
                }
                else
                {
                    message = prelude;
                }

                if (logEvent.Exception != null)
                {
                    message += FormatException(logEvent.Exception);
                }

                if (logEvent.Properties.TryGetValue("stackTrace", out var stackTrace))
                {
                    message += $"\n{string.Join("\n", Json.FromSerilogProperty("stackTrace", stackTrace, true) as JArray)}";
                }

                // Escape curly braces so defaultLogHandler.LogFormat doesn't interpret them as format specifiers
                message = message
                    .Replace("{", "{{")
                    .Replace("}", "}}");

                Logger.emittingToUnity = true;
                try
                {
                    Logger.defaultUnityLogHandler.LogFormat(logLevelMap[logEvent.Level], null, message);
                }
                finally
                {
                    Logger.emittingToUnity = false;
                }
            }

            static string FormatException(Exception exception)
            {
                var result = $"\n{exception.GetType().FullName}: {exception.Message}";

                if (exception.StackTrace != null)
                {
                    result += $"\n{exception.StackTrace}";
                }

                if (exception is AggregateException aggregate)
                {
                    foreach (var inner in aggregate.InnerExceptions)
                        result += FormatException(inner);
                }
                else if (exception.InnerException != null)
                {
                    result += "\n--- Inner Exception ---";
                    result += FormatException(exception.InnerException);
                }

                return result;
            }
        }
    }
}