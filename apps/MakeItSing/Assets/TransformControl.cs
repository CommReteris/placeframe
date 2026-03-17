using FofX.Stateful;
using Nessle;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public struct TransformControlProps
    {
        public ElementProps element;
        public TransformProps transform;
        public IListObservable<IControl> children;
    }

    public struct TransformProps
    {
        public IValueObservable<Vector3> localPosition;
        public IValueObservable<Quaternion> localRotation;
        public IValueObservable<Vector3> localScale;
    }

    public class TransformControl : Nessle.Control<TransformControlProps>
    {
        protected override void SetupInternal()
        {
            AddBinding(
                props.element.Subscribe(this),
                props.children?.Subscribe(
                    onAdd: (index, x) =>
                    {
                        x.rectTransform.SetParent(transform, false);
                        x.rectTransform.SetSiblingIndex(index);
                    },
                    onRemove: (index, x) => x.rectTransform.SetParent(null, false)
                ),
                props.transform.localPosition?.Subscribe(x => transform.localPosition = x),
                props.transform.localRotation?.Subscribe(x => transform.localRotation = x),
                props.transform.localScale?.Subscribe(x => transform.localScale = x)
            );
        }
    }
}