using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Outernet.Client
{
    public class UINavigationHelper : MonoBehaviour
    {
        void Update()
        {
            if (Keyboard.current.tabKey.wasPressedThisFrame)
            {
                var selected = EventSystem.current.currentSelectedGameObject;
                if (selected == null)
                    return;

                var selectable = selected.GetComponent<Selectable>();
                if (selectable == null)
                    return;

                var next = selectable.FindSelectableOnRight();

                if (next == null)
                    next = selectable.FindSelectableOnDown();

                if (next == null)
                    return;

                next.Select();
            }
        }
    }
}