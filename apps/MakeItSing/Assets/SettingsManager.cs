using System.IO;
using UnityEngine;
using SimpleJSON;
using FofX.Stateful;
using System;
using System.Linq;

namespace Plerion.MakeItSing
{
    public class SettingsManager : MonoBehaviour
    {
        private string settingsPath => $"{Application.persistentDataPath}/settings.json";

        private void Awake()
        {
            if (!File.Exists(settingsPath))
            {
                App.state.userSettings.ExecuteAction(x =>
                {
                    x.domain.value = null;
                    x.username.value = "user";
                    x.password.value = "password";
                });
            }
            else
            {
                App.state.userSettings.ExecuteAction(
                    JSONNode.Parse(File.ReadAllText(settingsPath)),
                    (json, settings) => settings.FromJSON(json)
                );
            }

            App.RegisterObserver(HandleSettingsChanged, App.state.userSettings);
            App.RegisterObserver(HandleRoomChanged, App.state.roomConnection.connectionString);
        }

        private void HandleRoomChanged(NodeChangeEventArgs args)
        {
            string room = App.state.roomConnection.connectionString.value;

            if (string.IsNullOrEmpty(room) || App.state.userSettings.recentRooms.Any(x => x.value == room))
                return;

            App.state.userSettings.recentRooms.ExecuteActionOrDelay(
                room,
                (room, recentRooms) => recentRooms.Add().value = room
            );
        }


        private void HandleSettingsChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
                return;

            File.WriteAllText(settingsPath, App.state.userSettings.ToJSON(_ => true).ToString());
        }
    }
}