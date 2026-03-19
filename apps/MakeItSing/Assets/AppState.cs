using System;
using FofX.Stateful;
using Unity.Mathematics;

namespace Plerion.MakeItSing
{
    public class RoomData : ObservableObject, IKeyedObservableNode<string>
    {
        public string roomName { get; private set; }
        public ObservablePrimitive<string> demo { get; private set; }
        public ObservablePrimitive<int> userCount { get; private set; }

        void IKeyedObservableNode<string>.AssignKey(string key)
            => roomName = key;
    }

    public class AppState : ObservableObject
    {
        public UserSettings userSettings { get; private set; }
        public ObservablePrimitive<bool> loggedIn { get; private set; }
        public ConnectionState nameServerConnection { get; private set; }
        public ConnectionState roomConnection { get; private set; }
        public ObservableList<ObservablePrimitive<string>> activeRooms { get; private set; }
        public ObservablePrimitive<double2> roughGrainedLocation { get; private set; }

        public ObservablePrimitive<int> playerID { get; private set; }
        public ObservablePrimitive<int> masterClientID { get; private set; }
        public ObservablePrimitive<bool> isMasterClient { get; private set; }

        public ObservablePrimitive<bool> initialSyncComplete { get; private set; }
        public ObservablePrimitive<bool> inRoomAndSynchronized { get; private set; }

        public SceneState scene { get; private set; }

        protected override void PostInitializeInternal()
        {
            nameServerConnection.shouldBeConnected.RegisterDerived(
                _ => nameServerConnection.shouldBeConnected.value = loggedIn.value && !string.IsNullOrEmpty(nameServerConnection.connectionString.value),
                ObservationScope.All,
                loggedIn,
                nameServerConnection.connectionString
            );

            roomConnection.shouldBeConnected.RegisterDerived(
                _ => roomConnection.shouldBeConnected.value = nameServerConnection.status.value == ConnectionStatus.Connected && !string.IsNullOrEmpty(roomConnection.connectionString.value),
                ObservationScope.All,
                nameServerConnection.status,
                roomConnection.connectionString
            );

            inRoomAndSynchronized.RegisterDerived(
                _ => inRoomAndSynchronized.value = roomConnection.connected.value && initialSyncComplete.value,
                ObservationScope.All,
                roomConnection.connected,
                initialSyncComplete
            );

            isMasterClient.RegisterDerived(
                _ => isMasterClient.value = playerID.value == masterClientID.value,
                ObservationScope.All,
                playerID,
                masterClientID
            );
        }
    }

    public enum ConnectionStatus
    {
        Disconnected,
        Connecting,
        Connected,
        Disconnecting,
        Error
    }

    public class ConnectionState : ObservableObject
    {
        public ObservablePrimitive<string> connectionString { get; private set; }
        public ObservablePrimitive<bool> shouldBeConnected { get; private set; }
        public ObservablePrimitive<ConnectionStatus> status { get; private set; }
        public ObservablePrimitive<bool> connected { get; private set; }
        public ObservablePrimitive<string> error { get; private set; }

        protected override void PostInitializeInternal()
        {
            connected.RegisterDerived(
                _ => connected.value = status.value == ConnectionStatus.Connected,
                ObservationScope.All,
                status
            );
        }
    }

    public class UserSettings : ObservableObject
    {
        public ObservablePrimitive<string> domain { get; private set; }
        public ObservablePrimitive<string> username { get; private set; }
        public ObservablePrimitive<string> password { get; private set; }
        public ObservableList<ObservablePrimitive<string>> recentRooms { get; private set; }
    }

    public class SceneState : ObservableObject
    {
        public ObservableDictionary<int, PlayerData> players { get; private set; }
        public ObservablePrimitiveMap<int, SceneObjectID> playersToAvatars { get; private set; }
    }

    public class PlayerData : ObservableObject, IKeyedObservableNode<int>
    {
        public int playerID { get; private set; }
        public ObservablePrimitive<bool> initialSyncComplete { get; private set; }

        public void AssignKey(int key)
            => playerID = key;
    }

    public struct SceneObjectID
    {
        public static SceneObjectID Empty => new SceneObjectID(0);

        public int value { get; }
        public bool IsEmpty => value == 0;

        public SceneObjectID(int value)
        {
            this.value = value;
        }
    }
}