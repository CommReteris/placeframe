using ObserveThing;
using ObserveThing.StatefulExtensions;

using FofX.Stateful;

namespace Plerion.MakeItSing
{
    public static class Extentions
    {
        public static ICollectionObservable<T> ExceptDynamic<T>(this ICollectionObservable<T> source, ICollectionObservable<T> except)
            => source.WhereDynamic(x => except.ContainsDynamic(x).SelectDynamic(x => !x));

        public static IListObservable<T> AsObservable<T>(this ObservableList<ObservablePrimitive<T>> source)
            => source.AsObservable<ObservablePrimitive<T>>().SelectDynamic(x => x.AsObservable());
    }
}