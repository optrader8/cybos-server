/**
 * WebSocket 클라이언트 - 실시간 시세 수신
 */

import { StockPrice } from "@/types/pair";

export type PriceUpdateCallback = (price: StockPrice) => void;

export class PriceWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private callbacks: Map<string, Set<PriceUpdateCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1초
  private isIntentionallyClosed = false;

  constructor(url: string = "ws://localhost:8000/ws/prices") {
    this.url = url;
  }

  /**
   * WebSocket 연결
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("WebSocket already connected");
      return;
    }

    this.isIntentionallyClosed = false;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log("✅ WebSocket connected");
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handlePriceUpdate(data);
        } catch (error) {
          console.error("Failed to parse message:", error);
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      this.ws.onclose = () => {
        console.log("WebSocket closed");
        if (!this.isIntentionallyClosed) {
          this.attemptReconnect();
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.attemptReconnect();
    }
  }

  /**
   * 재연결 시도
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnect attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * 종목 구독
   */
  subscribe(stockCode: string, callback: PriceUpdateCallback): void {
    if (!this.callbacks.has(stockCode)) {
      this.callbacks.set(stockCode, new Set());

      // 서버에 구독 요청
      this.send({
        action: "subscribe",
        stock_code: stockCode,
      });
    }

    this.callbacks.get(stockCode)!.add(callback);
  }

  /**
   * 종목 구독 해제
   */
  unsubscribe(stockCode: string, callback: PriceUpdateCallback): void {
    const callbacks = this.callbacks.get(stockCode);
    if (!callbacks) return;

    callbacks.delete(callback);

    if (callbacks.size === 0) {
      this.callbacks.delete(stockCode);

      // 서버에 구독 해제 요청
      this.send({
        action: "unsubscribe",
        stock_code: stockCode,
      });
    }
  }

  /**
   * 시세 업데이트 처리
   */
  private handlePriceUpdate(data: StockPrice): void {
    const { code } = data;
    const callbacks = this.callbacks.get(code);

    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error("Callback error:", error);
        }
      });
    }
  }

  /**
   * 메시지 전송
   */
  private send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket is not open. Cannot send message.");
    }
  }

  /**
   * 연결 종료
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.callbacks.clear();
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// 싱글톤 인스턴스
let priceWebSocket: PriceWebSocket | null = null;

export function getPriceWebSocket(): PriceWebSocket {
  if (!priceWebSocket) {
    priceWebSocket = new PriceWebSocket();
    priceWebSocket.connect();
  }
  return priceWebSocket;
}
