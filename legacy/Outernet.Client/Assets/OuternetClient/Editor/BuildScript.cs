using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.XR.Hands.OpenXR;
using UnityEngine.XR.OpenXR;
using UnityEngine.XR.OpenXR.Features;
using UnityEngine.XR.OpenXR.Features.Interactions;
using MagicLeap.OpenXR.Features;
using MagicLeap.OpenXR.InteractionProfiles;
using MagicLeap.OpenXR.Features.LocalizationMaps;
using MagicLeap.OpenXR.Features.MarkerUnderstanding;
using MagicLeap.OpenXR.Features.Planes;
using MagicLeap.OpenXR.Features.UserCalibration;

namespace Outernet.Client
{
    public static class Build
    {
        public static void BuildForMagicLeap()
        {
            PlayerSettings.productName = "Legacy Outernet Client";
            ConfigureForMagicLeap();
            BuildMain();
        }

        public static void BuildForAndroidMobile()
        {
            PlayerSettings.productName = "Legacy Outernet Client";
            ConfigureForAndroidMobile();
            BuildMain();
        }

        public static void BuildForLinux64()
        {
            PlayerSettings.productName = "Legacy Outernet Editor";
            ConfigureForLinux64();
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
            PlayerSettings.productName = "Legacy Outernet Editor";
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
            ConfigureForWin64();
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

        // [MenuItem("Build/MagicLeap", priority = 0)]
        // public static void StartBuildForMagicLeap()
        // {
        //     StartBuild("MagicLeap");
        // }

        // [MenuItem("Build/AndroidMobile", priority = 1)]
        // public static void StartBuildForAndroidMobile()
        // {
        //     StartBuild("AndroidMobile");
        // }

        [MenuItem("Build/Configure/MagicLeap", priority = 10)]
        public static void ConfigureForMagicLeap()
        {
            PlayerSettings.SetScriptingDefineSymbols(NamedBuildTarget.Android, "OUTERNET_MAGIC_LEAP;USE_INPUT_SYSTEM_POSE_CONTROL;USE_STICK_CONTROL_THUMBSTICKS;MAGIC_LEAP;USE_ML_OPENXR");

            var settings = XRGeneralSettingsPerBuildTarget.XRGeneralSettingsForBuildTarget(BuildTargetGroup.Android);
            XRPackageMetadataStore.RemoveLoader(settings.Manager, "Unity.XR.ARCore.ARCoreLoader", BuildTargetGroup.Android);
            XRPackageMetadataStore.AssignLoader(settings.Manager, "Unity.XR.OpenXR.OpenXRLoader", BuildTargetGroup.Android);

            var openXRSettings = OpenXRSettings.GetSettingsForBuildTargetGroup(BuildTargetGroup.Android);

            foreach (var feature in openXRSettings.GetFeatures<OpenXRFeature>())
            {
                feature.enabled = false;
            }

            openXRSettings.GetFeature<HandTracking>().enabled = true;
            openXRSettings.GetFeature<HandInteractionProfile>().enabled = true;
            openXRSettings.GetFeature<MagicLeapFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapRenderingExtensionsFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapControllerProfile>().enabled = true;
            openXRSettings.GetFeature<MagicLeapLocalizationMapFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapMarkerUnderstandingFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapPlanesFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapReferenceSpacesFeature>().enabled = true;
            openXRSettings.GetFeature<MagicLeapUserCalibrationFeature>().enabled = true;

            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.Vulkan });
            PlayerSettings.SetNormalMapEncoding(NamedBuildTarget.Android, NormalMapEncoding.DXT5nm);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.X86_64;
            EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.DXT;
            GraphicsSettings.defaultRenderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/MagicLeap_PipelineAsset.asset");
        }

        [MenuItem("Build/Configure/Linux64", priority = 12)]
        public static void ConfigureForLinux64()
        {
            GraphicsSettings.defaultRenderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/Linux_PipelineAsset.asset");
        }

        [MenuItem("Build/Configure/Win64", priority = 13)]
        public static void ConfigureForWin64()
        {
            GraphicsSettings.defaultRenderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/Windows_PipelineAsset.asset");
        }

        [MenuItem("Build/Configure/AndroidMobile", priority = 11)]
        public static void ConfigureForAndroidMobile()
        {
            PlayerSettings.SetScriptingDefineSymbols(NamedBuildTarget.Android, "OUTERNET_ANDROID_MOBILE;USE_INPUT_SYSTEM_POSE_CONTROL");
            var settings = XRGeneralSettingsPerBuildTarget.XRGeneralSettingsForBuildTarget(BuildTargetGroup.Android);
            XRPackageMetadataStore.RemoveLoader(settings.Manager, "Unity.XR.OpenXR.OpenXRLoader", BuildTargetGroup.Android);
            XRPackageMetadataStore.AssignLoader(settings.Manager, "Unity.XR.ARCore.ARCoreLoader", BuildTargetGroup.Android);

            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.SetNormalMapEncoding(NamedBuildTarget.Android, NormalMapEncoding.DXT5nm);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.ASTC;
            GraphicsSettings.defaultRenderPipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/AndroidMobile_PipelineAsset.asset");
        }

        private static void StartBuild(string platform)
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/C ubt --platform {platform} --wait-for-process-id {Process.GetCurrentProcess().Id} --reopen-with-build-target {EditorUserBuildSettings.activeBuildTarget}",
                UseShellExecute = true,
                WindowStyle = ProcessWindowStyle.Normal // Ensure the window is brought to the front
            });

            EditorApplication.Exit(0);
        }

        // public class LogHandler : ILogHandler
        // {
        //     private ILogHandler defaultLogHandler = UnityEngine.Debug.unityLogger.logHandler;

        //     public void LogException(Exception exception, UnityEngine.Object context)
        //     {
        //         defaultLogHandler.LogException(exception, context);
        //     }

        //     public void LogFormat(LogType logType, UnityEngine.Object context, string format, params object[] args)
        //     {
        //         string logMessage = string.Format(format, args);

        //         // Suppress Cesium package warnings like
        //         // "Plugin 'Packages/com.cesium.unity/Plugins/iOS/lib/libabsl_log_internal_nullguard.a' doesn't have CPU architecture set, since it's a native plugin, valid architecture is required, skipping."
        //         if (logMessage.Contains("Plugin 'Packages/com.cesium.unity")) return;

        //         // Suppress Cesium package warnings like
        //         // ""Shader warning in 'Cesium/CesiumUnlitTilesetShader': implicit truncation of vector type at Files/Unity/Hub/Editor/2022.3.27f1/Editor/Data/CGIncludes/UnityShadowLibrary.cginc(63)"
        //         if (logMessage.Contains("Shader warning in 'Cesium")) return;

        //         defaultLogHandler.LogFormat(logType, context, format, args);
        //     }
        // }

        private static void BuildMain()
        {
            Directory.CreateDirectory("Build");
            string sanitizedName = Regex.Replace(PlayerSettings.productName, @"[^a-zA-Z0-9._-]", "_");
            string outputPath = $"Build/{sanitizedName}.apk";

            Placeframe.BuildUtility.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new string[] { "Assets/OuternetClient/Main.unity" },
                locationPathName = outputPath,
                target = BuildTarget.Android,
                targetGroup = BuildTargetGroup.Android,
                options = BuildOptions.Development
            });
        }
    }
}
