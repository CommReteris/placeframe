using System;
using FofX.Stateful;
using Nessle;
using UnityEngine;
using ObserveThing.StatefulExtensions;

using static Nessle.UIBuilder;
using static Nessle.Props;
using static Outernet.Client.UIElements;
using UnityEngine.XR.Interaction.Toolkit.UI;

namespace Outernet.Client
{
    public class SystemUI : MonoBehaviour
    {
        private IControl _loginUI;

        private void Awake()
        {
            App.RegisterObserver(HandleLoggedInChanged, App.state.loggedIn);
        }

        private void HandleLoggedInChanged(NodeChangeEventArgs args)
        {
            if (App.state.loggedIn.value)
            {
                _loginUI?.Dispose();
                _loginUI = null;
                return;
            }

#if OUTERNET_MAGIC_LEAP
            _loginUI = ARLoginScreen();
#else
            _loginUI = MobileLoginScreen();
#endif
        }

        private IControl ARLoginScreen()
        {
            IControl canvas = default;

            var result = TransformControl(new()
            {
                transform =
                {
                    localPosition = Value(Camera.main.transform.position + (Camera.main.transform.forward.Flatten().normalized * 0.75f) + new Vector3(0, -.33f, 0)),
                    localRotation = Value(Quaternion.Euler(45f, 0, 0)),
                    localScale = Value(new Vector3(0.001f, 0.001f, 0.001f))
                },
                children = List(
                    canvas = Canvas(new()
                    {
                        renderMode = Value(RenderMode.WorldSpace),
                        layout =
                        {
                            sizeDelta = Value(new Vector2(500, 282)),
                            position = Value(Vector2.zero)
                        },
                        children = List(
                            LoginScreen(new()
                            {
                                layout = FillParent(),
                                contentPadding = Value(new RectOffset(20, 20, 0, 0)),
                                domain = App.state.userSettings.domain.ToObservable(),
                                username = App.state.userSettings.username.ToObservable(),
                                password = App.state.userSettings.password.ToObservable(),
                                onDomainChanged = x => App.state.userSettings.domain.ExecuteSetOrDelay(x),
                                onPasswordChanged = x => App.state.userSettings.password.ExecuteSetOrDelay(x),
                                onUsernameChanged = x => App.state.userSettings.username.ExecuteSetOrDelay(x),
                                loginMethod = (domain, username, password) => Utility.Login(domain, username, password)
                            })
                        )
                    })
                )
            });

            canvas.gameObject.AddComponent<TrackedDeviceGraphicRaycaster>();

            return result;
        }

        private IControl MobileLoginScreen()
        {
            return Canvas(new()
            {
                children = List(
                    LoginScreen(new()
                    {
                        layout = FillParent(),
                        contentPadding = Value(new RectOffset(20, 20, 0, 0)),
                        domain = App.state.userSettings.domain.ToObservable(),
                        username = App.state.userSettings.username.ToObservable(),
                        password = App.state.userSettings.password.ToObservable(),
                        onDomainChanged = x => App.state.userSettings.domain.ExecuteSetOrDelay(x),
                        onPasswordChanged = x => App.state.userSettings.password.ExecuteSetOrDelay(x),
                        onUsernameChanged = x => App.state.userSettings.username.ExecuteSetOrDelay(x),
                        loginMethod = (domain, username, password) => Utility.Login(domain, username, password)
                    })
                )
            });
        }
    }
}