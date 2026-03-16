using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Placeframe.Core;
using Unity.Mathematics;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class LocalizationManager : MonoBehaviour
    {
        private double MAP_LOAD_RADIUS = 100;
        private List<Guid> _loadedMaps = new List<Guid>();

        private void Awake()
        {
            App.RegisterObserver(HandleRoughGrainedLocationChanged, App.state.roughGrainedLocation);
        }

        private void HandleRoughGrainedLocationChanged(NodeChangeEventArgs args)
        {
            // VisualPositioningSystem.GetLocalizationMaps()
        }

        private async UniTask UpdateMaps(double latitude, double longitude, double radius, CancellationToken cancellationToken = default)
        {
            // Determine ground level (height above WGS84 ellipsoid) at the specified latitude and longitude
            SceneReferences.GroundTileset.suspendUpdate = false;
            var heightSamplingResult = await SceneReferences.GroundTileset.SampleHeightMostDetailed(
                new double3(longitude, latitude, 0)
            );
            var groundLevelHeightAboveWGS84Ellipsoid = heightSamplingResult.longitudeLatitudeHeightPositions[0].z;
            SceneReferences.GroundTileset.suspendUpdate = true;

            // Convert cartographic coordinates to ECEF coordinates, and use the ENU frame at that location for orientation
            var ecefPosition = WGS84.CartographicToEcef(
                CartographicCoordinates.FromLongitudeLatitudeHeight(
                    longitude,
                    latitude,
                    groundLevelHeightAboveWGS84Ellipsoid
                )
            );

            await VisualPositioningSystem.SetLocalizationMaps(ecefPosition, MAP_LOAD_RADIUS);
        }
    }
}