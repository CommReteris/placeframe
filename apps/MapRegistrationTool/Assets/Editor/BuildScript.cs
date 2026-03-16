using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Unity.Plastic.Newtonsoft.Json;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

namespace Placeframe.MapRegistrationTool
{
    public static class Build
    {
        public static void BuildForWin64()
        {
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);

            string outputPath = "Build/Win64/MapRegistrationTool.exe";
            Directory.CreateDirectory(Path.GetDirectoryName(outputPath));

            BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { "Assets/OuternetClient/Main.unity" },
                locationPathName = outputPath,
                target = BuildTarget.StandaloneWindows64,
                targetGroup = BuildTargetGroup.Standalone,
            });

            SerializableBuildReport serializableReport = new SerializableBuildReport();
            serializableReport.result = report.summary.result.ToString();
            (serializableReport.steps, serializableReport.messages) = BuildStepTree(new List<BuildStep>(report.steps), -1);
            File.WriteAllText("Build/Win64/BuildReport.json", JsonConvert.SerializeObject(serializableReport, Formatting.Indented));

            if (report.summary.result != BuildResult.Succeeded)
            {
                EditorApplication.Exit(1);
            }
        }

        [Serializable]
        public class SerializableBuildReport
        {
            public string result;
            public List<Step> steps;
            public List<Message> messages;
        }

        [Serializable]
        public class Step
        {
            public string name;
            public string duration;
            [JsonProperty(NullValueHandling = NullValueHandling.Ignore)] public List<Step> steps;
        }

        [Serializable]
        public class Message
        {
            public string content;
            public string type;
            public string step;
        }

        private static (List<Step>, List<Message>) BuildStepTree(List<BuildStep> reportBuildSteps, int depth)
        {
            List<Step> steps = new List<Step>();
            List<Message> messages = new List<Message>();

            while (reportBuildSteps.Count > 0)
            {
                if (reportBuildSteps[0].depth <= depth) break;

                BuildStep reportBuildStep = reportBuildSteps[0];
                reportBuildSteps.RemoveAt(0);

                messages.AddRange(reportBuildStep.messages
                    .Select(m => new Message
                    {
                        content = m.content,
                        type = m.type.ToString(),
                        step = reportBuildStep.name
                    }));

                var (subSteps, subMessages) = BuildStepTree(reportBuildSteps, reportBuildStep.depth);
                messages.AddRange(subMessages);

                steps.Add(new Step
                {
                    name = reportBuildStep.name,
                    duration = reportBuildStep.duration.TotalSeconds.ToString(),
                    steps = subSteps.Count > 0 ? subSteps : null
                });
            }

            return (steps, messages);
        }
    }
}
