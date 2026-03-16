using ObserveThing;
using ObserveThing.StatefulExtensions;

using FofX.Stateful;

namespace Plerion.MakeItSing
{
    public static class Extentions
    {
        public static ICollectionObservable<T> ObservableExcept<T>(this ICollectionObservable<T> source, ICollectionObservable<T> except)
            => source.ObservableWhere(x => except.ObservableContains(x).ObservableSelect(x => !x));

        public static IListObservable<T> ObservableExcept<T>(this IListObservable<T> source, IListObservable<T> except)
            => source.ObservableWhere(x => except.ObservableContains(x).ObservableSelect(x => !x)).ObservableOrderBy(x => source.ObservableIndexOf(x));

        public static IListObservable<T> ToObservable<T>(this ObservableList<ObservablePrimitive<T>> source)
            => Extensions.ToObservable(source).ObservableSelect(x => x.ToObservable());
    }
}