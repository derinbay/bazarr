import { io, Socket } from "socket.io-client";
import {
  badgeUpdateAll,
  siteUpdateOffline,
  systemUpdateTasks,
} from "../../@redux/actions";
import reduxStore from "../../@redux/store";
import { log } from "../../utilites/logger";

export class SocketIOClient {
  private socket: Socket;

  constructor(baseUrl: string) {
    this.socket = io({
      path: `${baseUrl}socket.io`,
      transports: ["websocket", "polling"],
    });

    this.socket.on("connect", this.onConnect.bind(this));
    this.socket.on("disconnect", this.onDisconnect.bind(this));
    this.socket.on("data", this.onDataEvent.bind(this));
  }

  reconnect() {
    this.socket.connect();
  }

  private dispatch(action: any) {
    reduxStore.dispatch(action);
  }

  onConnect() {
    log("info", "Socket.IO has connected");
    this.dispatch(siteUpdateOffline(false));
  }

  onDisconnect() {
    log("warning", "Socket.IO has disconnected");
    this.dispatch(siteUpdateOffline(true));
  }

  onDataEvent(event: SocketIOType.Body) {
    log("info", "Socket.IO receives", event);
    switch (event.type) {
      case "badges":
        this.dispatch(badgeUpdateAll());
        break;
      case "task":
        this.dispatch(systemUpdateTasks());
        break;
      default:
        log("error", "SocketIO receives a unhandle event", event);
    }
  }
}
