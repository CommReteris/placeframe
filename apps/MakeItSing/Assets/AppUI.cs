using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using static Nessle.Props;

using ObserveThing;
using ObserveThing.StatefulExtensions;

using FofX.Stateful;

using static Plerion.MakeItSing.UIElements;
using Placeframe.Core;
using System;
using Cysharp.Threading.Tasks;

namespace Plerion.MakeItSing
{
    public class AppUI : MonoBehaviour
    {
        private IControl _ui;
        private IControl _screen;

        private void Awake()
        {
            _ui = Canvas(new()
            {
                children = List(
                    Observables.Combine(
                        App.state.loggedIn.ToObservable(),
                        App.state.roomConnection.shouldBeConnected.ToObservable(),
                        App.state.roomConnection.status.ToObservable(),
                        (loggedIn, shouldConnectToRoom, connectionStatus) =>
                        {
                            _screen?.Dispose();

                            if (!loggedIn)
                            {
                                ValueObservable<string> loginErrorMessage = new ValueObservable<string>();

                                _screen = LoginUI(new()
                                {
                                    layout = FillParentProps(),
                                    domain = App.state.userSettings.domain.ToObservable(),
                                    username = App.state.userSettings.username.ToObservable(),
                                    password = App.state.userSettings.password.ToObservable(),
                                    onDomainChanged = x => App.state.userSettings.domain.ExecuteSetOrDelay(x),
                                    onUsernameChanged = x => App.state.userSettings.username.ExecuteSetOrDelay(x),
                                    onPasswordChanged = x => App.state.userSettings.password.ExecuteSetOrDelay(x),
                                    loginErrorMessage = loginErrorMessage,
                                    onLoginSelected = async () =>
                                    {
                                        loginErrorMessage.value = null;

                                        try
                                        {
                                            await VisualPositioningSystem.Login(
                                                App.state.userSettings.domain.value,
                                                App.state.userSettings.username.value,
                                                App.state.userSettings.password.value
                                            );
                                        }
                                        catch
                                        {
                                            await UniTask.SwitchToMainThread();
                                            loginErrorMessage.value = "Login failed";
                                            throw;
                                        }

                                        await UniTask.SwitchToMainThread();
                                        App.state.loggedIn.ExecuteSet(true);
                                    }
                                });
                            }
                            else if (!shouldConnectToRoom)
                            {
                                _screen = RoomSelectUI(new()
                                {
                                    layout = FillParentProps(),
                                    roomName = App.state.roomConnection.connectionString.ToObservable(),
                                    activeRooms = App.state.activeRooms.ToObservable(),
                                    recentRooms = App.state.userSettings.recentRooms.ToObservable().ObservableExcept(App.state.activeRooms.ToObservable()),
                                    onRoomSelected = x => App.state.roomConnection.connectionString.ExecuteSet(x)
                                });
                            }
                            else if (connectionStatus != ConnectionStatus.Connected)
                            {
                                _screen = ConnectingToRoomUI();
                            }
                            else
                            {
                                _screen = null;
                            }

                            return _screen;
                        }
                    )
                )
            });
        }
    }
}