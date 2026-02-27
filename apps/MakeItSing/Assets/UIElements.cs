using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using static Nessle.Props;
using ObserveThing;
using ObserveThing.StatefulExtensions;
using System;
using UnityEngine.Events;

namespace Plerion.MakeItSing
{
    public static class UIElements
    {
        public static UIElementSet elements;

        public static LayoutProps GetPlatformLayoutProps()
        {
            if (Application.isMobilePlatform)
            {
                return FillParentProps();
            }
            else
            {
                return new LayoutProps()
                {
                    anchorMin = Value(new Vector2(0.375f, 0)),
                    anchorMax = Value(new Vector2(0.625f, 1)),
                    offsetMin = Value(new Vector2(0, 0)),
                    offsetMax = Value(new Vector2(0, 0))
                };
            }
        }

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
                        Control(
                            "PlatformArea",
                            new()
                            {
                                layout = GetPlatformLayoutProps(),
                                children = List(
                                    VerticalLayout(new()
                                    {
                                        layout =
                                        {
                                            anchorMin = Value(new Vector2(0f, 0.5f)),
                                            anchorMax = Value(new Vector2(1f, 0.5f)),
                                            offsetMin = Value(new Vector2(0, 0)),
                                            offsetMax = Value(new Vector2(0, 0)),
                                            fitContentVertical = Value(UnityEngine.UI.ContentSizeFitter.FitMode.PreferredSize)
                                        },
                                        childAlignment = Value(TextAnchor.MiddleCenter),
                                        spacing = Value(10f),
                                        childControlWidth = Value(true),
                                        childControlHeight = Value(true),
                                        children = List(
                                            LabeledProperty(new()
                                            {
                                                label = Value("Domain"),
                                                labelWidth = Value(100f),
                                                content = Value(InputField(new()
                                                {
                                                    value = props.domain,
                                                    layout = { flexibleWidth = Value(true) },
                                                    onValueChanged = props.onDomainChanged
                                                }))
                                            }),
                                            LabeledProperty(new()
                                            {
                                                label = Value("Username"),
                                                labelWidth = Value(100f),
                                                content = Value(InputField(new()
                                                {
                                                    value = props.username,
                                                    layout = { flexibleWidth = Value(true) },
                                                    onValueChanged = props.onUsernameChanged
                                                }))
                                            }),
                                            LabeledProperty(new()
                                            {
                                                label = Value("Password"),
                                                labelWidth = Value(100f),
                                                content = Value(InputField(new()
                                                {
                                                    value = props.password,
                                                    layout = { flexibleWidth = Value(true) },
                                                    contentType = Value(TMPro.TMP_InputField.ContentType.Password),
                                                    onValueChanged = props.onPasswordChanged
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
                            }
                        )
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
                        Control(
                            "SafeArea",
                            new()
                            {
                                layout = GetPlatformLayoutProps(),
                                children = List(
                                    VerticalLayout(new()
                                    {
                                        childControlHeight = Value(true),
                                        childControlWidth = Value(true),
                                        spacing = Value(10f),
                                        layout =
                                        {
                                            anchorMin = Value(new Vector2(0, 0f)),
                                            anchorMax = Value(new Vector2(1, 0.5f)),
                                            offsetMin = Value(new Vector2(0, 0)),
                                            offsetMax = Value(new Vector2(0, 40f)) // center the input field in the middle of the screen
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
                                                        layout = { flexibleWidth = Value(true) },
                                                        spacing = Value(10f),
                                                        childAlignment = Value(TextAnchor.MiddleLeft),
                                                        childControlHeight = Value(true),
                                                        childControlWidth = Value(true),
                                                        children = List(
                                                            InputField(new()
                                                            {
                                                                value = props.roomName,
                                                                layout = { flexibleWidth = Value(true) },
                                                                onValueChanged = x => internalRoomName.value = x
                                                            }),
                                                            Button(new()
                                                            {
                                                                content = List(
                                                                    Text(new() { value = Value("Create") })
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
                                                    flexibleHeight = Value(true),
                                                    flexibleWidth = Value(true)
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
                                                            element = { active = props.activeRooms.ObservableCount().ObservableSelect(x => x > 0) },
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
                                                                    children = props.activeRooms.CreateDynamic(x => Button(new()
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
                                                                active = props.recentRooms.AsObservable().ObservableCount().ObservableSelect(x => x != 0)
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
                                                                    children = props.recentRooms.AsObservable()
                                                                        .CreateDynamic(x => Button(new()
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
                                    })
                                )
                            }
                        )
                    )
                }
            );
        }

        public static IControl ConnectingToRoomUI()
        {
            return null;
        }
    }
}