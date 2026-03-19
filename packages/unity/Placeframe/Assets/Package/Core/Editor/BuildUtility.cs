using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using Unity.Plastic.Newtonsoft.Json;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

namespace Placeframe
{
    public static class BuildUtility
    {
        public static void BuildPlayer(BuildPlayerOptions options)
        {
            // Verify no tracked files were dirtied by Unity's project open
            // string[] dirtyOnEntry = RunGit("diff --name-only")
            //     .Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            // if (dirtyOnEntry.Length > 0)
            // {
            //     UnityEngine.Debug.LogError($"Tracked files were dirty before build started (Unity project open mutated them — commit the normalized state):\n{string.Join("\n", dirtyOnEntry)}");
            //     EditorApplication.Exit(1);
            // }

            // Inject version from .build-version.json if present
            string projectRoot = Path.GetDirectoryName(UnityEngine.Application.dataPath);
            string versionFile = Path.Combine(projectRoot, ".build-version.json");
            if (File.Exists(versionFile))
            {
                string json = File.ReadAllText(versionFile);
                UnityEngine.Debug.Log($"InjectVersion: read {versionFile}: {json}");
                var data = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);

                if (data.TryGetValue("version", out object version))
                {
                    PlayerSettings.bundleVersion = version.ToString();
                    UnityEngine.Debug.Log($"Injected bundleVersion: {version}");
                }

                if (data.TryGetValue("runNumber", out object runNumber) && int.TryParse(runNumber.ToString(), out int code))
                {
                    PlayerSettings.Android.bundleVersionCode = code;
                    UnityEngine.Debug.Log($"Injected bundleVersionCode: {code}");
                }
            }

            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            AssetDatabase.SaveAssets();

            // Snapshot files dirtied by configure/inject (these are expected mutations)
            // var expectedChanges = new HashSet<string>(
            //     RunGit("diff --name-only").Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries));
            // if (expectedChanges.Count > 0)
            //     UnityEngine.Debug.Log($"Tracked files changed by configure/inject (expected):\n{string.Join("\n", expectedChanges)}");

            BuildReport report = BuildPipeline.BuildPlayer(options);

            // // Verify the build didn't dirty any files beyond what configure/inject changed
            // var postBuildChanges = new HashSet<string>(
            //     RunGit("diff --name-only").Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries));
            // var unexpected = postBuildChanges.Except(expectedChanges).ToList();
            // if (unexpected.Count > 0)
            // {
            //     UnityEngine.Debug.LogError($"Build introduced unexpected tracked-file changes:\n{string.Join("\n", unexpected)}");
            //     EditorApplication.Exit(1);
            // }

            // // Restore all files dirtied by configure/inject back to their committed state
            // if (expectedChanges.Count > 0)
            // {
            //     string fileList = string.Join(" ", expectedChanges.Select(f => $"\"{f}\""));
            //     RunGit($"checkout -- {fileList}");
            //     UnityEngine.Debug.Log($"Restored {expectedChanges.Count} tracked file(s) changed during build");
            // }

            // Write build report
            string reportPath = Path.Combine(Path.GetDirectoryName(options.locationPathName), "BuildReport.json");
            var serializableReport = new SerializableBuildReport();
            serializableReport.result = report.summary.result.ToString();
            (serializableReport.steps, serializableReport.messages) = BuildStepTree(new List<BuildStep>(report.steps), -1);
            File.WriteAllText(reportPath, JsonConvert.SerializeObject(serializableReport, Formatting.Indented));

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

        private static string RunGit(string arguments)
        {
            string projectDirectory = Path.GetDirectoryName(UnityEngine.Application.dataPath);
            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "git",
                    Arguments = arguments,
                    WorkingDirectory = projectDirectory,
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                }
            };
            process.Start();
            string output = process.StandardOutput.ReadToEnd();
            process.WaitForExit();
            return output;
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
