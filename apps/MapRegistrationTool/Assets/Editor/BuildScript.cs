using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Build;

namespace Placeframe.MapRegistrationTool
{
    public static class Build
    {
        public static void BuildForLinux64()
        {
            string sanitizedName = Regex.Replace(PlayerSettings.productName, @"[^a-zA-Z0-9._-]", "_");
            string outputPath = $"Build/{sanitizedName}";
            Directory.CreateDirectory("Build");

            Placeframe.BuildUtility.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { "Assets/OuternetClient/Main.unity" },
                locationPathName = outputPath,
                target = BuildTarget.StandaloneLinux64,
                targetGroup = BuildTargetGroup.Standalone,
            });
        }

        public static void BuildForWin64()
        {
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);

            string sanitizedName = Regex.Replace(PlayerSettings.productName, @"[^a-zA-Z0-9._-]", "_");
            string outputPath = $"Build/{sanitizedName}.exe";
            Directory.CreateDirectory("Build");

            Placeframe.BuildUtility.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { "Assets/OuternetClient/Main.unity" },
                locationPathName = outputPath,
                target = BuildTarget.StandaloneWindows64,
                targetGroup = BuildTargetGroup.Standalone,
            });
        }
    }
}
