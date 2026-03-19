using UnityEngine;

using System;
using System.IO;
using System.Linq;
using System.Threading;

using Cysharp.Threading.Tasks;

using FofX;
using FofX.Stateful;

using Photon.Realtime;
using Photon.Client;

using SimpleJSON;

namespace Plerion.MakeItSing
{
    public class ConnectionManager : IDisposable
    {
        private ConnectionState _connectionState;
        private Func<string, CancellationToken, UniTask> _connectMethod;
        private Func<CancellationToken, UniTask> _disconnectMethod;
        private TaskHandle _connectionTask = TaskHandle.Complete;

        public ConnectionManager(ConnectionState connectionState, Func<string, CancellationToken, UniTask> connectMethod, Func<CancellationToken, UniTask> disconnectMethod)
        {
            _connectionState = connectionState;
            _connectMethod = connectMethod;
            _disconnectMethod = disconnectMethod;

            connectionState.context.RegisterObserver(
                HandleShouldBeConnectedChanged,
                _connectionState.shouldBeConnected,
                _connectionState.connected
            );
        }

        private void HandleShouldBeConnectedChanged(NodeChangeEventArgs args)
        {
            _connectionTask.Cancel();

            if (_connectionState.shouldBeConnected.value)
            {
                _connectionTask = TaskHandle.Execute(Connect);
            }
            else
            {
                _connectionTask = TaskHandle.Execute(Disconnect);
            }
        }

        private async UniTask Connect(CancellationToken cancellationToken = default)
        {
            if (_connectionState.status.value == ConnectionStatus.Connected)
                return;

            _connectionState.ExecuteActionOrDelay(new SetConnectionStatusAction(ConnectionStatus.Connecting));

            try
            {
                await _connectMethod(_connectionState.connectionString.value, cancellationToken);
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();
                _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Error, exc.Message));

                throw;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Connected));
        }

        private async UniTask Disconnect(CancellationToken cancellationToken = default)
        {
            if (_connectionState.status.value == ConnectionStatus.Disconnected ||
                _connectionState.status.value == ConnectionStatus.Error)
            {
                return;
            }

            _connectionState.ExecuteActionOrDelay(new SetConnectionStatusAction(ConnectionStatus.Disconnecting));

            try
            {
                await _disconnectMethod(cancellationToken);
            }
            catch (Exception exc)
            {
                await UniTask.SwitchToMainThread();
                _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Error, exc.Message));

                throw;
            }

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            _connectionState.ExecuteAction(new SetConnectionStatusAction(ConnectionStatus.Disconnected));
        }

        public void Dispose()
        {
            _connectionTask.Cancel();
            _connectionState.context.DeregisterObserver(HandleShouldBeConnectedChanged);
        }
    }

    public class PhotonConnectionManager : MonoBehaviour, IInRoomCallbacks, IOnEventCallback
    {
        private const byte INITIAL_SYNC_EVENT = 1;
        private const byte INCREMENTAL_SYNC_EVENT = 2;

        private RealtimeClient _client;
        private ConnectionManager _nameserverConnection;
        private ConnectionManager _roomConnection;

        private MemoryStream _serializationStream = new MemoryStream();

        private void Awake()
        {
            AsyncSetup.Startup();

            _client = new RealtimeClient(ConnectionProtocol.Tcp);
            _client.AddCallbackTarget(this);

            _nameserverConnection = new ConnectionManager(
                App.state.nameServerConnection,
                (appID, _) => _client.ConnectUsingSettingsAsync(new AppSettings() { AppIdRealtime = appID }).AsUniTask(),
                _ => _client.DisconnectAsync().AsUniTask()
            );

            _roomConnection = new ConnectionManager(
                App.state.roomConnection,
                (roomID, _) => ConnectToRoom(roomID),
                _ => _client.LeaveRoomAsync().AsUniTask()
            );

            App.RegisterObserver(HandleSceneChanged, App.state.scene);
        }

        private void Update()
        {
            while (true)
            {
                if (!_client.DispatchIncomingCommands())
                    break;
            }
        }

        private void LateUpdate()
        {
            if (_serializationStream.Length > 0)
            {
                _client.OpRaiseEvent(
                    INCREMENTAL_SYNC_EVENT,
                    _serializationStream.ToArray(),
                    new RaiseEventArgs() { CachingOption = EventCaching.DoNotCache, Receivers = ReceiverGroup.Others },
                    new SendOptions() { DeliveryMode = DeliveryMode.Reliable }
                );

                _serializationStream.SetLength(0);
            }

            while (true)
            {
                if (!_client.SendOutgoingCommands())
                    break;
            }
        }

        private void OnDestroy()
        {
            _nameserverConnection.Dispose();
            _roomConnection.Dispose();
        }

        private async UniTask ConnectToRoom(string roomID)
        {
            await _client.ConnectToRoomAsync(new MatchmakingArguments() { RoomName = roomID, PhotonSettings = _client.AppSettings });
            await UniTask.SwitchToMainThread();
            App.state.playerID.ExecuteSet(_client.LocalPlayer.ActorNumber);
        }

        private bool _initialSyncComplete = false;

        private void HandleSceneChanged(NodeChangeEventArgs args)
        {
            if (!App.state.inRoomAndSynchronized.value || args.initialize)
                return;

            foreach (var change in args.changes)
            {
                if (change.source == App.state.initialSyncComplete)
                    _initialSyncComplete = (bool)change.currentValue;

                if (!_initialSyncComplete ||
                    change.changeType == ChangeType.Dispose ||
                    change.changeType == ChangeType.None)
                {
                    continue;
                }

                WriteChange(_serializationStream, change);
            }
        }

        private void WriteChange(MemoryStream stream, NodeChangeData change)
        {
            using (var writer = new BinaryWriter(stream))
            {
                writer.Write(change.source.nodePath);
                writer.Write(change.changeType == ChangeType.Remove);

                if (change.source is IObservablePrimitive prim)
                {
                    PhotonSerialization.GetSerializer(prim.primitiveType).Serialize(writer, change.currentValue, prim is IObservablePrimitiveArray);
                }
                else if (change.source is IObservableDictionary dict)
                {
                    PhotonSerialization.GetSerializer(dict.keyType).Serialize(writer, change.key, false);
                }
                else if (change.source is IObservableList list)
                {
                    PhotonSerialization.GetSerializer(typeof(int)).Serialize(writer, change.index.Value, false);
                }
                else if (change.source is IObservableSet set)
                {
                    PhotonSerialization.GetSerializer(set.itemType).Serialize(writer, change.collectionElement, false);
                }
                else if (change.source is IObservablePrimitiveMap map)
                {
                    var pair = (IPrimitiveMapPair)change.collectionElement;
                    PhotonSerialization.GetSerializer(map.leftType).Serialize(writer, pair.left, false);
                    PhotonSerialization.GetSerializer(map.rightType).Serialize(writer, pair.right, false);
                }
            }
        }

        private void SendInitialSync(int actorNumber)
        {
            var json = App.state.scene.ToJSON(x => !x.isDefault && !x.isDerived);
            _client.OpRaiseEvent(
                INITIAL_SYNC_EVENT,
                json,
                new RaiseEventArgs() { TargetActors = new int[] { actorNumber } },
                new SendOptions() { DeliveryMode = DeliveryMode.Reliable }
            );
        }

        // IInRoomCallbacks
        public void OnPlayerEnteredRoom(Player newPlayer)
        {
            if (_client.LocalPlayer.IsMasterClient)
                SendInitialSync(newPlayer.ActorNumber);
        }

        public void OnPlayerLeftRoom(Player otherPlayer)
        {
            App.ExecuteAction(new RemovePlayerAction(otherPlayer.ActorNumber));
        }

        public void OnPlayerPropertiesUpdate(Player targetPlayer, PhotonHashtable changedProps)
        {

        }

        public void OnMasterClientSwitched(Player newMasterClient)
        {
            App.ExecuteAction(new SetMasterClientAction(newMasterClient.ActorNumber));

            if (_client.LocalPlayer.IsMasterClient)
            {
                var unsyncedPlayers = _client.CurrentRoom.Players.Keys.Except(App.state.scene.players.keys).Where(x => x != _client.LocalPlayer.ActorNumber).ToArray();
                if (unsyncedPlayers.Length > 0)
                {
                    var json = App.state.scene.ToJSON(x => !x.isDefault && !x.isDerived);
                    _client.OpRaiseEvent(
                        INITIAL_SYNC_EVENT,
                        json,
                        new RaiseEventArgs() { TargetActors = unsyncedPlayers },
                        new SendOptions() { DeliveryMode = DeliveryMode.Reliable }
                    );
                }
            }
        }

        public void OnRoomPropertiesUpdate(PhotonHashtable propertiesThatChanged) { }

        // IOnEventCallback
        public void OnEvent(EventData photonEvent)
        {
            if (photonEvent.Code == INCREMENTAL_SYNC_EVENT)
            {
                App.ExecuteAction(new ApplyIncrementalSyncAction((byte[])photonEvent.CustomData));
            }
            else if (photonEvent.Code == INITIAL_SYNC_EVENT)
            {
                App.ExecuteAction(new CompleteInitialSyncAction(JSONNode.Parse((string)photonEvent.CustomData)));
            }
        }

        private class ApplyIncrementalSyncAction : ObservableNodeAction<AppState>
        {
            private byte[] _data;

            public ApplyIncrementalSyncAction(byte[] data)
            {
                _data = data;
            }

            public override void Execute(AppState state)
            {
                using (var stream = new MemoryStream(_data))
                using (var reader = new BinaryReader(stream))
                {
                    while (stream.Position < stream.Length)
                    {
                        var path = reader.ReadString();
                        var isRemove = reader.ReadBoolean();

                        if (!state.TryFindChild(path, out var dest))
                            throw new Exception($"Destination state not found. Path: {path}");

                        if (dest is IObservablePrimitive prim)
                        {
                            prim.SetValue(PhotonSerialization.GetSerializer(prim.primitiveType).Deserialize(reader, prim is IObservablePrimitiveArray));
                        }
                        else if (dest is IObservableDictionary dict)
                        {
                            dict.Add(PhotonSerialization.GetSerializer(dict.keyType).Deserialize(reader, false));
                        }
                        else if (dest is IObservableList list)
                        {
                            list.Insert((int)PhotonSerialization.GetSerializer(typeof(int)).Deserialize(reader, false));
                        }
                        else if (dest is IObservableSet set)
                        {
                            set.Add(PhotonSerialization.GetSerializer(set.itemType).Deserialize(reader, false));
                        }
                        else if (dest is IObservablePrimitiveMap map)
                        {
                            map.Add(
                                PhotonSerialization.GetSerializer(map.leftType).Deserialize(reader, false),
                                PhotonSerialization.GetSerializer(map.rightType).Deserialize(reader, false)
                            );
                        }
                    }
                }
            }
        }
    }

    public class RemovePlayerAction : ObservableNodeAction<AppState>
    {
        private int _playerID;

        public RemovePlayerAction(int playerID)
        {
            _playerID = playerID;
        }

        public override void Execute(AppState target)
        {
            target.scene.players.Remove(_playerID);
            //remove objects that this player owns here
        }
    }

    public class CompleteInitialSyncAction : ObservableNodeAction<AppState>
    {
        private JSONNode _sceneState;

        public CompleteInitialSyncAction(JSONNode sceneState)
        {
            _sceneState = sceneState;
        }

        public override void Execute(AppState target)
        {
            target.scene.FromJSON(_sceneState);
            target.initialSyncComplete.value = true;
            target.scene.players.Add(target.playerID.value);
            //set player fields here
        }
    }

    public class SetMasterClientAction : ObservableNodeAction<AppState>
    {
        private int _masterClientID;

        public SetMasterClientAction(int masterClientID)
        {
            _masterClientID = masterClientID;
        }

        public override void Execute(AppState target)
        {
            target.masterClientID.value = _masterClientID;
            if (target.isMasterClient.value)
                target.initialSyncComplete.value = true;
        }
    }
}