/**
 * 페어 트레이딩 관련 타입 정의
 */

export enum PairStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  MONITORING = "MONITORING",
  SUSPENDED = "SUSPENDED",
}

export enum PairType {
  TWO_WAY = "2-WAY",
  THREE_WAY = "3-WAY",
  FOUR_WAY = "4-WAY",
  N_WAY = "N-WAY",
}

export interface PairInfo {
  pair_id: string;
  pair_type: PairType;
  stock_codes: string[];
  status: PairStatus;
  name?: string;
  description?: string;

  // 공적분 정보
  cointegration_score: number;
  half_life: number;
  hedge_ratios: number[];

  // 통계 정보
  correlation: number;
  spread_mean: number;
  spread_std: number;

  // 성과 정보
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_trades: number;

  // 시간 정보
  created_at?: string;
  updated_at?: string;
  last_analyzed_at?: string;
}

export interface CointegrationResult {
  result_id: string;
  pair_id: string;
  stock_codes: string[];
  method: string;
  test_statistic: number;
  p_value: number;
  critical_values: Record<string, number>;
  cointegration_vector: number[];
  hedge_ratios: number[];
  half_life: number;
  sample_size: number;
  start_date: string;
  end_date: string;
  significance: string;
  created_at: string;
}

export enum SignalType {
  ENTRY_LONG = "ENTRY_LONG",
  ENTRY_SHORT = "ENTRY_SHORT",
  EXIT_LONG = "EXIT_LONG",
  EXIT_SHORT = "EXIT_SHORT",
  STOP_LOSS = "STOP_LOSS",
  TAKE_PROFIT = "TAKE_PROFIT",
}

export enum SignalStatus {
  ACTIVE = "ACTIVE",
  EXECUTED = "EXECUTED",
  CANCELLED = "CANCELLED",
  EXPIRED = "EXPIRED",
}

export interface PairSignal {
  signal_id: string;
  pair_id: string;
  stock_codes: string[];
  signal_type: SignalType;
  status: SignalStatus;

  // 가격 정보
  current_prices: Record<string, number>;
  entry_prices: Record<string, number>;
  target_prices: Record<string, number>;
  stop_prices: Record<string, number>;

  // 스프레드 정보
  spread: number;
  spread_mean: number;
  spread_std: number;
  z_score: number;

  // 포지션 정보
  position_sizes: Record<string, number>;
  hedge_ratios: number[];

  // 시간 정보
  created_at: string;
  executed_at?: string;
  expired_at?: string;

  // 메타데이터
  confidence: number;
  expected_return: number;
  risk_level: number;
  notes: string;
}

export interface StockPrice {
  code: string;
  name: string;
  time: string;
  current_price: number;
  change: number;
  change_rate: number;
  volume: number;
  amount: number;
}
