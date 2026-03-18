using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using static Nessle.Props;
using ObserveThing;
using System;
using UnityEngine.Events;
using UnityEngine.XR.Interaction.Toolkit.Samples.SpatialKeyboard;
using TMPro;

namespace Plerion.MakeItSing
{
    public static class UIElements
    {
        public static UIElementSet elements;

        public struct LoginUIProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> domain;
            public IValueObservable<string> username;
            public IValueObservable<string> password;
            public IValueObservable<string> loginErrorMessage;
            public UnityAction<string> onDomainChanged;
            public UnityAction<string> onUsernameChanged;
            public UnityAction<string> onPasswordChanged;
            public UnityAction onLoginSelected;
        }

        public static IControl LoginUI(LoginUIProps props)
        {
            return Control(
                "LoginUI",
                new()
                {
                    element = props.element,
                    layout = props.layout,
                    children = List(
                        Image(new()
                        {
                            style = { color = Value(elements.backgroundColor) },
                            layout = FillParentProps()
                        }),
                        VerticalLayout(new()
                        {
                            layout = FillParentProps(),
                            childAlignment = Value(TextAnchor.MiddleCenter),
                            childControlWidth = Value(true),
                            childControlHeight = Value(true),
                            padding = Value(new RectOffset(20, 20, 0, 0)),
                            spacing = Value(25f),
                            children = List(
                                Text(new()
                                {
                                    value = Value("Outernet"),
                                    style =
                                    {
                                        fontSize = Value(40f),
                                        horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center)
                                    }
                                }),
                                VerticalLayout(new()
                                {
                                    layout =
                                    {
                                        flexibleWidth = Value(0f),
                                        preferredWidth = Value(600f)
                                    },
                                    spacing = Value(10f),
                                    childAlignment = Value(TextAnchor.MiddleCenter),
                                    childControlWidth = Value(true),
                                    childControlHeight = Value(true),
                                    children = List(
                                        LabeledProperty(new()
                                        {
                                            label = Value("Domain"),
                                            labelWidth = Value(75f),
                                            content = Value(PlatformInputField(new()
                                            {
                                                inputField =
                                                {
                                                    value = props.domain,
                                                    layout = { flexibleWidth = Value(1f) },
                                                    onValueChanged = props.onDomainChanged
                                                }
                                            }))
                                        }),
                                        LabeledProperty(new()
                                        {
                                            label = Value("Username"),
                                            labelWidth = Value(75f),
                                            content = Value(PlatformInputField(new()
                                            {
                                                inputField =
                                                {
                                                    value = props.username,
                                                    layout = { flexibleWidth = Value(1f) },
                                                    onValueChanged = props.onUsernameChanged
                                                }
                                            }))
                                        }),
                                        LabeledProperty(new()
                                        {
                                            label = Value("Password"),
                                            labelWidth = Value(75f),
                                            content = Value(PlatformInputField(new()
                                            {
                                                inputField =
                                                {
                                                    value = props.password,
                                                    layout = { flexibleWidth = Value(1f) },
                                                    contentType = Value(TMPro.TMP_InputField.ContentType.Password),
                                                    onValueChanged = props.onPasswordChanged
                                                }
                                            }))
                                        }),
                                        HorizontalLayout(new()
                                        {
                                            childControlHeight = Value(true),
                                            childControlWidth = Value(true),
                                            childAlignment = Value(TextAnchor.MiddleCenter),
                                            children = List(
                                                Button(new()
                                                {
                                                    onClick = props.onLoginSelected,
                                                    content = List(Text(new() { value = Value("Login") }))
                                                })
                                            )
                                        }),
                                        Text(new()
                                        {
                                            element = { active = props.loginErrorMessage.ObservableSelect(x => !string.IsNullOrEmpty(x)) },
                                            value = props.loginErrorMessage,
                                            style =
                                            {
                                                color = Value(Color.red),
                                                horizontalAlignment = Value(TMPro.HorizontalAlignmentOptions.Center),
                                                verticalAlignment = Value(TMPro.VerticalAlignmentOptions.Baseline)
                                            }
                                        })
                                    )
                                })
                            )
                        })
                    )
                }
            );
        }

        public static LayoutProps FillParentProps(LayoutProps from = default)
        {
            from.anchorMin = from.anchorMin ?? Value(new Vector2(0, 0));
            from.anchorMax = from.anchorMax ?? Value(new Vector2(1, 1));
            from.offsetMin = from.offsetMin ?? Value(new Vector2(0, 0));
            from.offsetMax = from.offsetMax ?? Value(new Vector2(0, 0));

            return from;
        }

        public struct LabeledPropertyProps
        {
            public ElementProps element;
            public LayoutProps layout;
            public IValueObservable<string> label;
            public IValueObservable<float> labelWidth;
            public IValueObservable<IControl> content;
        }

        public static IControl LabeledProperty(LabeledPropertyProps props)
        {
            return HorizontalLayout(new()
            {
                element = props.element,
                layout = props.layout,
                childAlignment = Value(TextAnchor.MiddleLeft),
                spacing = Value(10f),
                childControlWidth = Value(true),
                childControlHeight = Value(true),
                children = List(
                    Value(Text(new()
                    {
                        value = props.label,
                        layout =
                        {
                            preferredWidth = props.labelWidth,
                            minWidth = props.labelWidth
                        }
                    })),
                    props.content
                )
            });
        }

        public struct RoomSelectUIProps
        {
            public ElementProps element;
            public LayoutProps layout;

            public IValueObservable<string> roomName;

            public IListObservable<string> activeRooms;
            public IListObservable<string> recentRooms;

            public Action<string> onRoomSelected;
        }

        public static IControl RoomSelectUI(RoomSelectUIProps props)
        {
            ValueObservable<string> internalRoomName = new ValueObservable<string>();

            return Control(
                "RoomSelectUI",
                new()
                {
                    element = props.element,
                    layout = props.layout,
                    children = List(
                        Image(new()
                        {
                            style = { color = Value(elements.backgroundColor) },
                            layout = FillParentProps()
                        }),
                        VerticalLayout(new()
                        {
                            childControlHeight = Value(true),
                            childControlWidth = Value(true),
                            childAlignment = Value(TextAnchor.MiddleCenter),
                            layout = FillParentProps(),
                            padding = Value(new RectOffset(20, 20, 0, 0)),
                            children = List(
                                Control(
                                    "SafeArea",
                                    new()
                                    {
                                        layout =
                                        {
                                            preferredWidth = Value(600f),
                                            flexibleWidth = Value(0f),
                                            flexibleHeight = Value(1f)
                                        },
                                        children = List(
                                            VerticalLayout(new()
                                            {
                                                childControlHeight = Value(true),
                                                childControlWidth = Value(true),
                                                spacing = Value(10f),
                                                childAlignment = Value(TextAnchor.LowerLeft),
                                                padding = Value(new RectOffset(0, 0, 0, 10)),
                                                layout =
                                                {
                                                    anchorMin = Value(new Vector2(0f, 0.5f)),
                                                    anchorMax = Value(new Vector2(1f, 1f)),
                                                    offsetMin = Value(new Vector2(0f, 0f)),
                                                    offsetMax = Value(new Vector2(0f, 0f)),
                                                    pivot = Value(new Vector2(0.5f, 0f))
                                                },
                                                children = List(
                                                    Text(new() { value = Value("Join Room") }),
                                                    LabeledProperty(new()
                                                    {
                                                        label = Value("Room Name"),
                                                        labelWidth = Value(100f),
                                                        content = Value(
                                                            HorizontalLayout(new()
                                                            {
                                                                layout = { flexibleWidth = Value(1f) },
                                                                spacing = Value(10f),
                                                                childAlignment = Value(TextAnchor.MiddleLeft),
                                                                childControlHeight = Value(true),
                                                                childControlWidth = Value(true),
                                                                children = List(
                                                                    PlatformInputField(new()
                                                                    {
                                                                        inputField =
                                                                        {
                                                                            value = props.roomName,
                                                                            layout = { flexibleWidth = Value(1f) },
                                                                            onValueChanged = x => internalRoomName.value = x
                                                                        }
                                                                    }),
                                                                    Button(new()
                                                                    {
                                                                        onClick = () => props.onRoomSelected?.Invoke(internalRoomName.value),
                                                                        content = List(
                                                                            Text(new() { value = Value("Create") })
                                                                        )
                                                                    })
                                                                )
                                                            })
                                                        )
                                                    })
                                                )
                                            }),
                                            ScrollRect(new()
                                            {
                                                horizontal = Value(false),
                                                vertical = Value(true),
                                                layout =
                                                {
                                                    anchorMin = Value(new Vector2(0, 0f)),
                                                    anchorMax = Value(new Vector2(1, 0.5f)),
                                                    offsetMin = Value(new Vector2(0, 0)),
                                                    offsetMax = Value(new Vector2(0, 0))
                                                },
                                                content = Value(VerticalLayout(new()
                                                {
                                                    childControlWidth = Value(true),
                                                    childControlHeight = Value(true),
                                                    childForceExpandWidth = Value(true),
                                                    layout =
                                                    {
                                                        pivot = Value(new Vector2(0, 1)),
                                                        anchorMin = Value(new Vector2(0, 1)),
                                                        anchorMax = Value(new Vector2(1, 1)),
                                                        offsetMin = Value(new Vector2(0, 0)),
                                                        offsetMax = Value(new Vector2(0, 0)),
                                                        fitContentVertical = Value(UnityEngine.UI.ContentSizeFitter.FitMode.PreferredSize)
                                                    },
                                                    children = List(
                                                        VerticalLayout(new()
                                                        {
                                                            element = { active = props.activeRooms?.ObservableCount().ObservableSelect(x => x > 0) },
                                                            childControlHeight = Value(true),
                                                            childControlWidth = Value(true),
                                                            childForceExpandWidth = Value(true),
                                                            spacing = Value(10f),
                                                            children = List(
                                                                Text(new() { value = Value("Active") }),
                                                                VerticalLayout(new()
                                                                {
                                                                    childControlHeight = Value(true),
                                                                    childControlWidth = Value(true),
                                                                    childForceExpandWidth = Value(true),
                                                                    spacing = Value(10f),
                                                                    children = props.activeRooms?.ObservableCreate(x => Button(new()
                                                                    {
                                                                        content = List(Text(new() { value = Value(x), })),
                                                                        onClick = () => props.onRoomSelected?.Invoke(x)
                                                                    }))
                                                                })
                                                            )
                                                        }),
                                                        VerticalLayout(new()
                                                        {
                                                            element = {
                                                                active = props.recentRooms?.ObservableCount().ObservableSelect(x => x != 0)
                                                            },
                                                            childControlHeight = Value(true),
                                                            childControlWidth = Value(true),
                                                            spacing = Value(10f),
                                                            children = List(
                                                                Text(new() { value = Value("Recent") }),
                                                                VerticalLayout(new()
                                                                {
                                                                    childControlHeight = Value(true),
                                                                    childControlWidth = Value(true),
                                                                    childForceExpandWidth = Value(true),
                                                                    spacing = Value(10f),
                                                                    children = props.recentRooms?
                                                                        .ObservableCreate(x => Button(new()
                                                                        {
                                                                            content = List(Text(new() { value = Value(x), })),
                                                                            onClick = () => props.onRoomSelected?.Invoke(x)
                                                                        }))
                                                                })
                                                            )
                                                        })
                                                    )
                                                }))
                                            })
                                        )
                                    }
                                )
                            )
                        })
                    )
                }
            );
        }

        public static IControl ConnectingToRoomUI()
        {
            return null;
        }

        public static IControl TransformControl(TransformControlProps props)
        {
            var gameObject = new GameObject("TransformControl");
            var control = gameObject.AddComponent<TransformControl>();
            control.Setup(props);
            return control;
        }

        public struct PlatformInputFieldProps
        {
            public InputFieldProps inputField;

            // The below values are ignored if we're not on magic leap
            public IValueObservable<bool> useSceneKeyboard;
            public IValueObservable<XRKeyboard> keyboard;
            public IValueObservable<bool> updateOnKeyPress;
            public IValueObservable<bool> alwaysObserveKeyboard;
            public IValueObservable<bool> monitorInputFieldCharacterLimit;
            public IValueObservable<bool> clearTextOnSubmit;
            public IValueObservable<bool> clearTextOnOpen;
        }

        public static IControl PlatformInputField(PlatformInputFieldProps props)
        {
            var inputField = InputField(props.inputField);

#if PLERION_MAGIC_LEAP
            var keyboardDisplay = inputField.gameObject.AddComponent<XRKeyboardDisplay>();
            keyboardDisplay.inputField = inputField.gameObject.GetComponent<TMP_InputField>();

            inputField.AddBinding(
                props.useSceneKeyboard?.Subscribe(x => keyboardDisplay.useSceneKeyboard = x),
                props.keyboard?.Subscribe(x => keyboardDisplay.keyboard = x),
                props.updateOnKeyPress?.Subscribe(x => keyboardDisplay.updateOnKeyPress = x),
                props.alwaysObserveKeyboard?.Subscribe(x => keyboardDisplay.alwaysObserveKeyboard = x),
                props.monitorInputFieldCharacterLimit?.Subscribe(x => keyboardDisplay.monitorInputFieldCharacterLimit = x),
                props.clearTextOnSubmit?.Subscribe(x => keyboardDisplay.clearTextOnSubmit = x),
                props.clearTextOnOpen?.Subscribe(x => keyboardDisplay.clearTextOnOpen = x)
            );
#endif

            return inputField;
        }
    }
}