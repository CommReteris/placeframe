using System;
using System.IO;
using FofX.Stateful;
using UnityEngine;

namespace Outernet.Client
{
    public class UserSettingsManager : MonoBehaviour
    {
        private const string USER_SETTINGS = "user_settings.json";
        private static string USER_SETTINGS_PATH => $"{Application.persistentDataPath}/{USER_SETTINGS}";

        private void Awake()
        {
            App.RegisterObserver(HandleUserSettingsChanged, App.state.userSettings);

            if (File.Exists(USER_SETTINGS_PATH))
            {
                App.ExecuteAction(new LoadUserSettingsAction(File.ReadAllText(USER_SETTINGS_PATH)));
            }
            else
            {
                App.state.userSettingsLoaded.ExecuteSetOrDelay(true);
            }
        }

        private void HandleUserSettingsChanged(NodeChangeEventArgs args)
        {
            if (!App.state.userSettingsLoaded.value)
                return;

            File.WriteAllText(USER_SETTINGS_PATH, App.state.userSettings.ToJSON(x => !x.isDefault && !x.isDerived).ToString());
        }
    }
}