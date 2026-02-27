using Outernet.Shared;
using Unity.Mathematics;
using UnityEngine;

namespace Outernet.Client
{
    public static class MathUtilityExtensions
    {
        public static Vector3 ToFloats(this double3 vector) => new Vector3((float)vector.x, (float)vector.y, (float)vector.z);
        public static double3 ToDoubles(this Vector3 vector) => new double3(vector.x, vector.y, vector.z);
        public static Double3 ToDouble3(this double3 vector) => new Double3(vector.x, vector.y, vector.z);
    }
}