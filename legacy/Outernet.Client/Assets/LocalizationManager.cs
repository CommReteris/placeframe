using System;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Placeframe.Core;
using UnityEngine;

namespace Outernet.Client
{
    public class LocalizationManager : MonoBehaviour
    {
        private void Awake()
        {
            App.RegisterObserver(HandleApiReadyChanged, App.state.apiReady);
        }

        private void HandleApiReadyChanged(NodeChangeEventArgs args)
        {
            if (App.state.apiReady.value)
                LoadMaps().Forget(); // This will ultimately be predicated on App.state.roughGrainedLocation
        }

        private async UniTask LoadMaps()
        {
            var maps = await App.API.GetLocalizationMapsAsync();

            foreach (var map in maps)
                VisualPositioningSystem.AddLocalizationMap(map.Id);
        }
    }
}
