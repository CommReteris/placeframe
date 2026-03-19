using UnityEngine;
using UnityEditor;

namespace Placeframe.Client
{
    [CustomEditor(typeof(AppSetup))]
    public class AppSetupEditor : Editor
    {
        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();
        }
    }
}