using System;
using FofX;
using FofX.Stateful;
using Placeframe.Core;

namespace Plerion.MakeItSing
{
    public class App : AppBase<AppState>
    {
        protected override void Awake()
        {
            base.Awake();

            RegisterObserver(HandleLoggedInChanged, state.loggedIn);
        }

        protected override void InitializeState(AppState state)
        {
            state.Initialize("root", new ObservableNodeContext());
        }

        private void HandleLoggedInChanged(NodeChangeEventArgs args)
        {
            if (state.loggedIn.value)
            {
                VisualPositioningSystem.StartLocalizing(1f);
            }
            else
            {
                VisualPositioningSystem.StopLocalizing();
            }
        }
    }
}