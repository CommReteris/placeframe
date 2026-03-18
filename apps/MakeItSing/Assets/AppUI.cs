using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using static Nessle.Props;

using ObserveThing;
using ObserveThing.StatefulExtensions;

using FofX.Stateful;

using static Plerion.MakeItSing.UIElements;
using Placeframe.Core;
using Cysharp.Threading.Tasks;
using UnityEngine.XR.Interaction.Toolkit.UI;

namespace Plerion.MakeItSing
{
    public class AppUI : MonoBehaviour
    {
        private IControl _ui;
        private IControl _screen;

        private void Awake()
        {
            _ui = PlatformCanvas(new()
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

        private IControl PlatformCanvas(CanvasProps props)
        {
#if PLERION_MAGIC_LEAP
            var camera = Camera.main.transform;
            var position = camera.forward;

            position.y = 0;
            position = position.normalized * 0.66f;
            position.y = camera.position.y - .33f;

            props.worldCamera = props.worldCamera ?? Value(Camera.main);
            props.renderMode = props.renderMode ?? Value(RenderMode.WorldSpace);
            props.layout.position = props.layout.position ?? Value(Vector2.zero);
            props.layout.scale = props.layout.scale ?? Value(new Vector2(1f, 1f));
            props.layout.sizeDelta = props.layout.sizeDelta ?? Value(new Vector2(960, 540));

            IControl canvas = default;

            var control = TransformControl(new()
            {
                transform =
                {
                    localPosition = Value(position),
                    localRotation = Value(Quaternion.LookRotation(position - camera.position, Vector3.up)),
                    localScale = Value(new Vector3(0.001f, 0.001f, 0.001f))
                },
                children = List(canvas = Canvas(props))
            });

            canvas.gameObject.AddComponent<TrackedDeviceGraphicRaycaster>();

            return control;
#else
            return Canvas(props);
#endif
        }
    }
}