using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

public static class CompileForAndroidMono
{
    public static void Run()
    {
        PlayerSettings.SetScriptingBackend(
            BuildTargetGroup.Android,
            ScriptingImplementation.Mono2x);
        PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARMv7;

        string buildPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(buildPath);
        try
        {
            BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                locationPathName = Path.Combine(buildPath, "game"),
                targetGroup = BuildTargetGroup.Android,
                target = BuildTarget.Android,
                scenes = new[] { "Assets/Scenes/Empty.unity" }
            });
        }
        finally
        {
            if (Directory.Exists(buildPath))
                Directory.Delete(buildPath, true);
        }
        EditorApplication.Exit(0);
    }
}

public class ExitAfterScriptCompilation : IPostBuildPlayerScriptDLLs
{
    public int callbackOrder => int.MaxValue;

    public void OnPostBuildPlayerScriptDLLs(BuildReport report)
    {
        EditorApplication.Exit(0);
    }
}
