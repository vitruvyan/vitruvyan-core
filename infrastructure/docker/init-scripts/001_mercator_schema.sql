-- =============================================================================
-- Mercator PostgreSQL Schema
-- =============================================================================
-- Auto-generated from vitruvyan production schema (PG 14)
-- Target: PostgreSQL 16 (mercator_postgres container)
-- Database: mercator / User: mercator_user
-- 
-- This schema includes all 89 tables from the vitruvyan system.
-- Tables will be populated incrementally as services are migrated.
--
-- Origin: pg_dump --schema-only --no-owner --no-privileges -d vitruvyan
-- Generated: Feb 2026
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
--
-- Name: asset_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.asset_type AS ENUM (
    'stock',
    'etf',
    'fund'
);
--
-- Name: replication_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.replication_type AS ENUM (
    'physical',
    'synthetic',
    'n/a'
);
--
-- Name: cleanup_old_langgraph_workflows(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.cleanup_old_langgraph_workflows() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM langgraph_workflows
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$;
--
-- Name: get_autopilot_limits(character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_autopilot_limits(p_user_id character varying) RETURNS TABLE(max_position_size numeric, max_daily_trades integer, risk_tolerance character varying, autonomous_enabled boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.max_position_size,
        s.max_daily_trades,
        s.risk_tolerance,
        s.autonomous_mode
    FROM user_autopilot_settings s
    WHERE s.user_id = p_user_id;
END;
$$;
--
-- Name: get_batch_explorer_url(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_batch_explorer_url(p_batch_id integer) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_txid VARCHAR(64);
    v_network VARCHAR(20);
    v_url TEXT;
BEGIN
    SELECT blockchain_txid, blockchain_network
    INTO v_txid, v_network
    FROM ledger_anchors
    WHERE id = p_batch_id;
    
    IF v_network = 'mainnet' THEN
        v_url := 'https://tronscan.org/#/transaction/' || v_txid;
    ELSE
        v_url := 'https://nile.tronscan.org/#/transaction/' || v_txid;
    END IF;
    
    RETURN v_url;
END;
$$;
--
-- Name: is_autonomous_mode(character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.is_autonomous_mode(p_user_id character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN (
        SELECT autonomous_mode 
        FROM user_autopilot_settings 
        WHERE user_id = p_user_id 
          AND autopilot_enabled = TRUE
    );
END;
$$;
--
-- Name: update_shadow_position_market_value(text, text, numeric); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_shadow_position_market_value(p_user_id text, p_ticker text, p_current_price numeric) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  UPDATE shadow_positions
  SET 
    market_value = quantity * p_current_price,
    unrealized_pnl = (quantity * p_current_price) - total_cost,
    unrealized_pnl_pct = ((quantity * p_current_price) - total_cost) / total_cost,
    last_updated = NOW()
  WHERE user_id = p_user_id AND ticker = p_ticker;
END;
$$;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: user_autopilot_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_autopilot_settings (
    user_id character varying(255) NOT NULL,
    autopilot_enabled boolean DEFAULT false,
    autonomous_mode boolean DEFAULT false,
    max_position_size numeric(5,4) DEFAULT 0.20,
    max_daily_trades integer DEFAULT 3,
    risk_tolerance character varying(50) DEFAULT 'balanced'::character varying,
    allowed_sectors jsonb,
    blocked_tickers jsonb,
    telegram_notifications boolean DEFAULT true,
    email_notifications boolean DEFAULT false,
    demo_mode boolean DEFAULT false,
    demo_cash_initial numeric(15,2) DEFAULT 50000.00,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    emergency_stop_active boolean DEFAULT false,
    telegram_chat_id bigint
);
--
-- Name: active_autonomous_users; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.active_autonomous_users AS
 SELECT user_autopilot_settings.user_id,
    user_autopilot_settings.risk_tolerance,
    user_autopilot_settings.max_daily_trades,
    user_autopilot_settings.demo_mode,
    user_autopilot_settings.created_at
   FROM public.user_autopilot_settings
  WHERE ((user_autopilot_settings.autopilot_enabled = true) AND (user_autopilot_settings.autonomous_mode = true));
--
-- Name: tickers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tickers (
    ticker text NOT NULL,
    company_name text,
    market text,
    sector text,
    country text,
    active boolean DEFAULT true,
    type public.asset_type,
    isin text,
    exchange text,
    mic text,
    currency text,
    domicile text,
    ter_bps integer,
    distributing boolean,
    replication public.replication_type,
    esg_label boolean,
    fund_category text,
    benchmark text,
    provider text,
    srri smallint,
    yahoo_symbol text,
    aliases text[],
    industry text,
    logo_url text
);
--
-- Name: active_tickers; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.active_tickers AS
 SELECT tickers.ticker
   FROM public.tickers
  WHERE (tickers.active = true);
--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);
--
-- Name: allocation_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.allocation_results (
    id integer NOT NULL,
    user_id text NOT NULL,
    tickers text[] NOT NULL,
    weights jsonb NOT NULL,
    mode text NOT NULL,
    amount numeric,
    currency text DEFAULT 'USD'::text,
    weaver_context jsonb,
    input_text text,
    created_at timestamp with time zone DEFAULT now()
);
--
-- Name: allocation_results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.allocation_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: allocation_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.allocation_results_id_seq OWNED BY public.allocation_results.id;
--
-- Name: audit_findings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_findings (
    id integer NOT NULL,
    audit_session_id integer,
    category character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    recommendation text,
    auto_correctable boolean DEFAULT false,
    corrected boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    ledger_batch_id integer
);
--
-- Name: audit_findings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_findings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: audit_findings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_findings_id_seq OWNED BY public.audit_findings.id;
--
-- Name: vault_audit_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_audit_history (
    id integer NOT NULL,
    audit_type character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    data jsonb,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: audit_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: audit_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_history_id_seq OWNED BY public.vault_audit_history.id;
--
-- Name: audit_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_sessions (
    id integer NOT NULL,
    audit_type character varying(50) DEFAULT 'quick'::character varying NOT NULL,
    status character varying(20) DEFAULT 'running'::character varying NOT NULL,
    findings jsonb DEFAULT '{}'::jsonb,
    metrics jsonb DEFAULT '{}'::jsonb,
    compliance_score double precision DEFAULT 0.0,
    execution_time_seconds integer DEFAULT 0,
    triggered_by character varying(100) DEFAULT 'manual'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    completed_at timestamp without time zone
);
--
-- Name: audit_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: audit_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_sessions_id_seq OWNED BY public.audit_sessions.id;
--
-- Name: autopilot_actions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.autopilot_actions (
    action_id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    action_type character varying(50) NOT NULL,
    ticker character varying(10),
    quantity numeric(15,4),
    estimated_price numeric(15,4),
    total_value numeric(15,2),
    rationale text,
    insight_id integer,
    status character varying(50) DEFAULT 'pending'::character varying,
    autonomous_mode boolean DEFAULT false,
    proposed_at timestamp with time zone DEFAULT now(),
    executed_at timestamp with time zone,
    execution_result jsonb,
    vee_narrative text,
    is_demo_mode boolean DEFAULT false,
    target_weight numeric(5,4),
    risk_score numeric(5,2),
    expected_impact jsonb,
    notes text
);
--
-- Name: autopilot_actions_action_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.autopilot_actions_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: autopilot_actions_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.autopilot_actions_action_id_seq OWNED BY public.autopilot_actions.action_id;
--
-- Name: babel_analysis_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.babel_analysis_log (
    id integer NOT NULL,
    query_text text NOT NULL,
    user_id character varying(255),
    correlation_id character varying(255),
    language_detected character varying(10),
    language_confidence double precision,
    sentiment_label character varying(50),
    sentiment_score double precision,
    fusion_boost double precision,
    embedding_used boolean DEFAULT false,
    babel_status character varying(50),
    cultural_context text,
    processing_time_ms integer,
    event_latency_ms integer,
    fusion_duration_ms integer,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: babel_analysis_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.babel_analysis_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: babel_analysis_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.babel_analysis_log_id_seq OWNED BY public.babel_analysis_log.id;
--
-- Name: backtest_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backtest_results (
    id integer NOT NULL,
    user_id text,
    ticker text NOT NULL,
    strategy_metrics jsonb,
    summary text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source text,
    raw_output jsonb
);
--
-- Name: backtest_results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.backtest_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: backtest_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.backtest_results_id_seq OWNED BY public.backtest_results.id;
--
-- Name: vault_backup_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_backup_history (
    id integer NOT NULL,
    backup_type character varying(20) NOT NULL,
    file_path text NOT NULL,
    file_hash text NOT NULL,
    size_mb double precision NOT NULL,
    duration_s double precision NOT NULL,
    triggered_by character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'completed'::character varying,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: backup_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.backup_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: backup_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.backup_history_id_seq OWNED BY public.vault_backup_history.id;
--
-- Name: block_trades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.block_trades (
    id integer NOT NULL,
    ticker text NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    volume bigint NOT NULL,
    price numeric(12,4),
    trade_type text,
    source text DEFAULT 'IEX'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: block_trades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.block_trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: block_trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.block_trades_id_seq OWNED BY public.block_trades.id;
--
-- Name: coherence_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.coherence_logs (
    id integer NOT NULL,
    status text NOT NULL,
    postgresql_count integer,
    qdrant_count integer,
    drift_percentage double precision,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: coherence_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.coherence_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: coherence_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.coherence_logs_id_seq OWNED BY public.coherence_logs.id;
--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    user_id text NOT NULL,
    prompt text,
    llm_response text,
    report text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    qdrant_id text,
    input_text text,
    slots jsonb,
    intent text,
    language character varying(10) DEFAULT 'en'::character varying
);
--
-- Name: conversations_archive; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations_archive (
    id integer NOT NULL,
    conv_id text,
    user_id text,
    role text,
    content text,
    conv_title text,
    created_at timestamp without time zone
);
--
-- Name: conversations_archive_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.conversations_archive_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: conversations_archive_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.conversations_archive_id_seq OWNED BY public.conversations_archive.id;
--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;
--
-- Name: daily_prices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.daily_prices (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    price numeric(12,4) NOT NULL,
    open numeric(12,4),
    high numeric(12,4),
    low numeric(12,4),
    volume bigint,
    "timestamp" timestamp without time zone DEFAULT now(),
    source character varying(50) DEFAULT 'yfinance'::character varying,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: daily_prices_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.daily_prices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: daily_prices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.daily_prices_id_seq OWNED BY public.daily_prices.id;
--
-- Name: dark_pool_volume; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dark_pool_volume (
    id integer NOT NULL,
    ticker text NOT NULL,
    date date NOT NULL,
    dark_pool_volume bigint,
    total_volume bigint,
    dark_pool_ratio numeric(5,4),
    source text DEFAULT 'IEX'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: dark_pool_volume_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dark_pool_volume_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: dark_pool_volume_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dark_pool_volume_id_seq OWNED BY public.dark_pool_volume.id;
--
-- Name: dependency_scans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dependency_scans (
    id integer NOT NULL,
    audit_session_id integer,
    scan_type character varying(50) NOT NULL,
    vulnerabilities_found integer DEFAULT 0,
    critical_count integer DEFAULT 0,
    high_count integer DEFAULT 0,
    medium_count integer DEFAULT 0,
    low_count integer DEFAULT 0,
    scan_results jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: dependency_scans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dependency_scans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: dependency_scans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dependency_scans_id_seq OWNED BY public.dependency_scans.id;
--
-- Name: design_points; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.design_points (
    id integer NOT NULL,
    designpoint_id text NOT NULL,
    run_id text,
    "timestamp" timestamp without time zone,
    generated_by text,
    meta_model_version text,
    kpi_model_version text,
    sampling_plan text,
    seed integer,
    code_version text,
    scenario_id text,
    scenario_horizon real,
    scenario_demand_rate real,
    scenario_critical_share real,
    disruption_events_json jsonb,
    node_hub_capacity_scale real,
    node_storage_scale real,
    node_availability_floor real,
    node_overrides_json jsonb,
    arc_capacity_scale real,
    arc_travel_time_scale real,
    arc_risk_index_scale real,
    arc_availability_floor real,
    arc_overrides_json jsonb,
    fleet_scale real,
    human_scale real,
    fuel_budget real,
    maintenance_factor real,
    vehicles_trucks integer,
    vehicles_vans integer,
    vehicles_helicopters integer,
    personnel_drivers integer,
    personnel_logisticians integer,
    personnel_specialists integer,
    personnel_shift_severity real,
    c2_availability real,
    comms_availability real,
    cyber_latency_ms real,
    situational_awareness real,
    decision_cycle text,
    doctrine text,
    hard_constraints_enabled boolean,
    thr_max_tempo_massimo integer,
    thr_min_coverage real,
    thr_min_impact_critical real,
    thr_max_saturation real,
    thr_max_bottleneck integer,
    thr_min_resilience real,
    thr_min_residual_capacity real,
    thr_max_fuel real,
    thr_max_idle_time integer,
    w_time_max real,
    w_coverage real,
    w_throughput real,
    w_resilience real,
    w_saturation real,
    w_capacity_residual real,
    kpi_tempo_medio_risposta real,
    kpi_tempo_massimo_risposta real,
    kpi_copertura_territoriale real,
    kpi_throughput_logistico real,
    kpi_saturazione_nodi real,
    kpi_utilizzo_mezzi real,
    kpi_colli_di_bottiglia real,
    kpi_impatto_missioni_critiche real,
    kpi_resilienza_whatif real,
    kpi_capacita_residua_flotta_nodi real,
    kpi_disponibilita_risorse_umane real,
    kpi_consumo_carburante_totale real,
    kpi_ore_uomo_impiegate real,
    kpi_tempo_inattivita_mezzi_personale real,
    kpi_tempo_medio_risposta_n real,
    kpi_tempo_massimo_risposta_n real,
    kpi_copertura_territoriale_n real,
    kpi_throughput_logistico_n real,
    kpi_saturazione_nodi_n real,
    kpi_utilizzo_mezzi_n real,
    kpi_colli_di_bottiglia_n real,
    kpi_impatto_missioni_critiche_n real,
    kpi_resilienza_whatif_n real,
    kpi_capacita_residua_flotta_nodi_n real,
    kpi_disponibilita_risorse_umane_n real,
    kpi_consumo_carburante_totale_n real,
    kpi_ore_uomo_impiegate_n real,
    kpi_tempo_inattivita_mezzi_personale_n real,
    is_pareto boolean,
    pareto_front_id text,
    selected_fema boolean,
    selected_nato boolean,
    selected_risk_aware boolean,
    best_rule text,
    score_fema real,
    score_nato real,
    score_risk_aware real,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: design_points_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.design_points_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: design_points_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.design_points_id_seq OWNED BY public.design_points.id;
--
-- Name: docs_archive; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.docs_archive (
    id integer NOT NULL,
    doc_title text NOT NULL,
    content text NOT NULL,
    source_file text,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: docs_archive_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.docs_archive_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: docs_archive_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.docs_archive_id_seq OWNED BY public.docs_archive.id;
--
-- Name: earnings_calendar; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.earnings_calendar (
    id integer NOT NULL,
    ticker text NOT NULL,
    earnings_date date NOT NULL,
    fiscal_quarter text,
    estimated_eps numeric(10,4),
    actual_eps numeric(10,4),
    surprise_pct numeric(6,2),
    source text DEFAULT 'YAHOO'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: earnings_calendar_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.earnings_calendar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: earnings_calendar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.earnings_calendar_id_seq OWNED BY public.earnings_calendar.id;
--
-- Name: expedition_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expedition_log (
    id integer NOT NULL,
    service_name text,
    correlation_id text,
    expedition_data text,
    total_records integer,
    status text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: expedition_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expedition_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: expedition_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expedition_log_id_seq OWNED BY public.expedition_log.id;
--
-- Name: explanations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.explanations (
    id integer NOT NULL,
    ticker text,
    explanation_gpt text,
    explanation_gpt_ts date DEFAULT CURRENT_DATE,
    summary text,
    technical text,
    detailed text,
    level smallint,
    agent text DEFAULT 'ExplainabilityEngine'::text,
    created_at timestamp with time zone DEFAULT now(),
    language character varying(5) DEFAULT 'it'::character varying,
    confidence_level double precision DEFAULT 0.0,
    dominant_factor double precision DEFAULT 0.0
);
--
-- Name: explanations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.explanations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: explanations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.explanations_id_seq OWNED BY public.explanations.id;
--
-- Name: factor_explanations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.factor_explanations (
    id integer NOT NULL,
    run_id integer NOT NULL,
    ticker text NOT NULL,
    rationale text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: factor_explanations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.factor_explanations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: factor_explanations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.factor_explanations_id_seq OWNED BY public.factor_explanations.id;
--
-- Name: factor_scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.factor_scores (
    id integer NOT NULL,
    ticker text NOT NULL,
    date date NOT NULL,
    value numeric,
    growth numeric,
    size numeric,
    quality numeric,
    momentum numeric,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: factor_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.factor_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: factor_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.factor_scores_id_seq OWNED BY public.factor_scores.id;
--
-- Name: fundamentals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fundamentals (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    date date NOT NULL,
    revenue numeric(15,2),
    revenue_growth_yoy numeric(8,4),
    revenue_growth_qoq numeric(8,4),
    eps numeric(10,4),
    eps_growth_yoy numeric(8,4),
    eps_growth_qoq numeric(8,4),
    gross_margin numeric(6,4),
    operating_margin numeric(6,4),
    net_margin numeric(6,4),
    ebitda_margin numeric(6,4),
    debt_to_equity numeric(8,4),
    current_ratio numeric(8,4),
    free_cash_flow numeric(15,2),
    dividend_yield numeric(6,4),
    dividend_rate numeric(10,4),
    payout_ratio numeric(6,4),
    pe_ratio numeric(8,4),
    pb_ratio numeric(8,4),
    peg_ratio numeric(8,4),
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: fundamentals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fundamentals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: fundamentals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fundamentals_id_seq OWNED BY public.fundamentals.id;
--
-- Name: gemma_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gemma_logs (
    id integer NOT NULL,
    user_id text,
    input_text text,
    intent text,
    tickers text[],
    horizon text,
    budget numeric,
    raw_output jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: gemma_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.gemma_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: gemma_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.gemma_logs_id_seq OWNED BY public.gemma_logs.id;
--
-- Name: guardian_insights; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.guardian_insights (
    insight_id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    insight_type character varying(50) NOT NULL,
    ticker character varying(10),
    severity character varying(20) NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    action_recommended text,
    metrics jsonb,
    user_action character varying(50) DEFAULT 'pending'::character varying,
    is_demo_mode boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    snapshot_id integer,
    recommendations jsonb,
    vee_explanations jsonb DEFAULT '{}'::jsonb,
    conversational_summary text
);
--
-- Name: guardian_insights_insight_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.guardian_insights_insight_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: guardian_insights_insight_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.guardian_insights_insight_id_seq OWNED BY public.guardian_insights.insight_id;
--
-- Name: intake_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intake_sessions (
    session_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying(100) NOT NULL,
    trace_id character varying(50),
    intake_state jsonb DEFAULT '{}'::jsonb NOT NULL,
    can_phase character varying(20) DEFAULT 'intake'::character varying NOT NULL,
    domain_profile character varying(50),
    last_question character varying(50),
    sections_completed integer[],
    uncertain_fields jsonb DEFAULT '{}'::jsonb,
    confidence_scores jsonb DEFAULT '{}'::jsonb,
    language character varying(10) DEFAULT 'en'::character varying,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    committed_at timestamp without time zone,
    run_id uuid,
    revision_count integer DEFAULT 0,
    total_questions_asked integer DEFAULT 0
);
--
-- Name: langgraph_workflows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.langgraph_workflows (
    workflow_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying(255) NOT NULL,
    intent character varying(50) NOT NULL,
    route_sequence jsonb NOT NULL,
    final_state jsonb NOT NULL,
    duration_seconds double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);
--
-- Name: langgraph_workflow_stats_by_user; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.langgraph_workflow_stats_by_user AS
 SELECT langgraph_workflows.user_id,
    count(*) AS total_workflows,
    avg(langgraph_workflows.duration_seconds) AS avg_duration_seconds,
    count(*) FILTER (WHERE ((langgraph_workflows.final_state ->> 'route'::text) = 'autopilot'::text)) AS autopilot_triggered,
    count(*) FILTER (WHERE ((langgraph_workflows.final_state ->> 'execution_mode'::text) = 'auto'::text)) AS auto_executed,
    count(*) FILTER (WHERE ((langgraph_workflows.final_state ->> 'max_severity'::text) = 'critical'::text)) AS critical_alerts,
    max(langgraph_workflows.created_at) AS last_workflow_at
   FROM public.langgraph_workflows
  WHERE (langgraph_workflows.created_at > (now() - '30 days'::interval))
  GROUP BY langgraph_workflows.user_id
  ORDER BY (count(*)) DESC;
--
-- Name: langgraph_workflows_recent; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.langgraph_workflows_recent AS
 SELECT langgraph_workflows.workflow_id,
    langgraph_workflows.user_id,
    langgraph_workflows.intent,
    jsonb_array_length(langgraph_workflows.route_sequence) AS nodes_visited,
    (langgraph_workflows.final_state ->> 'max_severity'::text) AS max_severity,
    (langgraph_workflows.final_state ->> 'execution_mode'::text) AS execution_mode,
    langgraph_workflows.duration_seconds,
    langgraph_workflows.created_at
   FROM public.langgraph_workflows
  WHERE (langgraph_workflows.created_at > (now() - '7 days'::interval))
  ORDER BY langgraph_workflows.created_at DESC
 LIMIT 100;
--
-- Name: trend_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trend_logs (
    id integer NOT NULL,
    user_id text,
    ticker text,
    short_trend text,
    medium_trend text,
    long_trend text,
    sma_short numeric,
    sma_medium numeric,
    sma_long numeric,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    raw_output jsonb
);
--
-- Name: latest_trend; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.latest_trend AS
 SELECT DISTINCT ON (trend_logs.ticker) trend_logs.id,
    trend_logs.ticker,
    trend_logs.short_trend,
    trend_logs.medium_trend,
    trend_logs.long_trend,
    trend_logs.sma_short,
    trend_logs.sma_medium,
    trend_logs.sma_long,
    trend_logs."timestamp"
   FROM public.trend_logs
  ORDER BY trend_logs.ticker, trend_logs."timestamp" DESC;
--
-- Name: ledger_anchors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ledger_anchors (
    id integer NOT NULL,
    batch_size integer NOT NULL,
    trace_ids text[] NOT NULL,
    merkle_root character varying(64) NOT NULL,
    blockchain_txid character varying(64) NOT NULL,
    blockchain_network character varying(20) NOT NULL,
    anchored_at timestamp without time zone DEFAULT now() NOT NULL,
    verified boolean DEFAULT false,
    verified_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);
--
-- Name: ledger_anchors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ledger_anchors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: ledger_anchors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ledger_anchors_id_seq OWNED BY public.ledger_anchors.id;
--
-- Name: ledger_pending_events; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.ledger_pending_events AS
 SELECT count(*) AS unanchored_count,
    min(audit_findings.created_at) AS oldest_event_at,
    max(audit_findings.created_at) AS newest_event_at
   FROM public.audit_findings
  WHERE (audit_findings.ledger_batch_id IS NULL);
--
-- Name: ledger_recent_activity; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.ledger_recent_activity AS
SELECT
    NULL::integer AS batch_id,
    NULL::integer AS event_count,
    NULL::character varying(64) AS merkle_root,
    NULL::character varying(64) AS txid,
    NULL::character varying(20) AS network,
    NULL::timestamp without time zone AS anchored_at,
    NULL::boolean AS verified,
    NULL::bigint AS events_linked;
--
-- Name: log_agent; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.log_agent (
    id bigint NOT NULL,
    agent text NOT NULL,
    ticker text,
    payload_json jsonb,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    trace_id character varying(255),
    user_id character varying(255)
);
--
-- Name: log_agent_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.log_agent_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: log_agent_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.log_agent_id_seq OWNED BY public.log_agent.id;
--
-- Name: macro_outlook; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macro_outlook (
    id integer NOT NULL,
    date date NOT NULL,
    inflation_rate numeric,
    interest_rate numeric,
    market_volatility numeric,
    source text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: macro_outlook_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.macro_outlook_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: macro_outlook_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.macro_outlook_id_seq OWNED BY public.macro_outlook.id;
--
-- Name: mcp_tool_calls; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mcp_tool_calls (
    conclave_id uuid NOT NULL,
    tool_name character varying(100) NOT NULL,
    args jsonb NOT NULL,
    result jsonb NOT NULL,
    orthodoxy_status character varying(20) NOT NULL,
    user_id character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);
--
-- Name: mcp_recent_calls; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.mcp_recent_calls AS
 SELECT mcp_tool_calls.conclave_id,
    mcp_tool_calls.tool_name,
    mcp_tool_calls.orthodoxy_status,
    mcp_tool_calls.user_id,
    mcp_tool_calls.created_at,
    EXTRACT(epoch FROM (now() - (mcp_tool_calls.created_at)::timestamp with time zone)) AS seconds_ago
   FROM public.mcp_tool_calls
  WHERE (mcp_tool_calls.created_at > (now() - '24:00:00'::interval))
  ORDER BY mcp_tool_calls.created_at DESC;
--
-- Name: mcp_tool_stats; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.mcp_tool_stats AS
 SELECT mcp_tool_calls.tool_name,
    count(*) AS total_calls,
    count(*) FILTER (WHERE ((mcp_tool_calls.orthodoxy_status)::text = 'blessed'::text)) AS blessed_calls,
    count(*) FILTER (WHERE ((mcp_tool_calls.orthodoxy_status)::text = 'heretical'::text)) AS heretical_calls,
    count(DISTINCT mcp_tool_calls.user_id) AS unique_users,
    max(mcp_tool_calls.created_at) AS last_call
   FROM public.mcp_tool_calls
  GROUP BY mcp_tool_calls.tool_name
  ORDER BY (count(*)) DESC;
--
-- Name: memory_sync_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.memory_sync_logs (
    id integer NOT NULL,
    sync_type text NOT NULL,
    items_synced integer,
    duration_seconds double precision,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: memory_sync_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.memory_sync_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: memory_sync_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.memory_sync_logs_id_seq OWNED BY public.memory_sync_logs.id;
--
-- Name: momentum_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.momentum_logs (
    id integer NOT NULL,
    user_id text,
    ticker text,
    rsi numeric,
    signal text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    raw_output jsonb,
    horizon text,
    roc numeric,
    macd numeric,
    macd_signal numeric,
    roc_trend text,
    macd_trend text
);
--
-- Name: momentum_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.momentum_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: momentum_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.momentum_logs_id_seq OWNED BY public.momentum_logs.id;
--
-- Name: ohlcv_daily; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ohlcv_daily (
    ticker text NOT NULL,
    dt date NOT NULL,
    open double precision,
    high double precision,
    low double precision,
    close double precision,
    adj_close double precision,
    volume bigint,
    currency text,
    source text DEFAULT 'yfinance'::text,
    created_at timestamp with time zone DEFAULT now()
);
--
-- Name: options_flow; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.options_flow (
    id integer NOT NULL,
    ticker text NOT NULL,
    date date NOT NULL,
    call_volume bigint,
    put_volume bigint,
    call_open_interest bigint,
    put_open_interest bigint,
    call_put_ratio numeric(6,4),
    source text DEFAULT 'POLYGON'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: options_flow_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.options_flow_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: options_flow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.options_flow_id_seq OWNED BY public.options_flow.id;
--
-- Name: pending_guardian_insights; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.pending_guardian_insights AS
 SELECT guardian_insights.insight_id,
    guardian_insights.user_id,
    guardian_insights.insight_type,
    guardian_insights.severity,
    guardian_insights.title,
    guardian_insights.created_at,
    (EXTRACT(epoch FROM (now() - guardian_insights.created_at)) / (3600)::numeric) AS hours_pending
   FROM public.guardian_insights
  WHERE (((guardian_insights.user_action)::text = 'pending'::text) AND ((guardian_insights.severity)::text = ANY ((ARRAY['high'::character varying, 'critical'::character varying])::text[])))
  ORDER BY
        CASE guardian_insights.severity
            WHEN 'critical'::text THEN 1
            WHEN 'high'::text THEN 2
            ELSE NULL::integer
        END, guardian_insights.created_at;
--
-- Name: perception_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.perception_logs (
    id integer NOT NULL,
    perception_id uuid NOT NULL,
    test_id character varying(100) NOT NULL,
    user_id character varying(100) NOT NULL,
    sensor_type character varying(50) NOT NULL,
    lat numeric(10,7),
    lon numeric(11,7),
    accuracy double precision,
    audio_duration_ms integer,
    audio_format character varying(20),
    image_width integer,
    image_height integer,
    device_timestamp timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    vee_summary text,
    confidence double precision DEFAULT 0.0,
    metadata jsonb DEFAULT '{}'::jsonb
);
--
-- Name: perception_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.perception_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: perception_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.perception_logs_id_seq OWNED BY public.perception_logs.id;
--
-- Name: phrases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.phrases (
    id integer NOT NULL,
    phrase_text text NOT NULL,
    context_type text,
    sentiment text,
    tone text,
    source text,
    created_at timestamp with time zone DEFAULT now(),
    language text,
    embedded boolean DEFAULT false,
    phrase_hash text,
    embedding_id bigint,
    ticker text
);
--
-- Name: phrases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.phrases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: phrases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.phrases_id_seq OWNED BY public.phrases.id;
--
-- Name: plasticity_adjustments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plasticity_adjustments (
    id integer NOT NULL,
    consumer_name text NOT NULL,
    parameter_name text NOT NULL,
    old_value double precision,
    new_value double precision NOT NULL,
    adjustment_reason text,
    is_manual boolean DEFAULT false,
    override_reason text,
    overridden_by text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT plasticity_adjustments_new_value_check CHECK (((new_value >= (0.0)::double precision) AND (new_value <= (1.0)::double precision)))
);
--
-- Name: plasticity_adjustments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plasticity_adjustments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: plasticity_adjustments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plasticity_adjustments_id_seq OWNED BY public.plasticity_adjustments.id;
--
-- Name: plasticity_anomalies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plasticity_anomalies (
    id integer NOT NULL,
    detected_at timestamp with time zone DEFAULT now() NOT NULL,
    anomaly_type character varying(30) NOT NULL,
    consumer_name character varying(100) NOT NULL,
    parameter_name character varying(100) NOT NULL,
    severity double precision NOT NULL,
    evidence jsonb NOT NULL,
    recommendation text,
    resolved_at timestamp with time zone,
    resolution_notes text
);
--
-- Name: plasticity_anomalies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plasticity_anomalies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: plasticity_anomalies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plasticity_anomalies_id_seq OWNED BY public.plasticity_anomalies.id;
--
-- Name: plasticity_anomaly_actions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plasticity_anomaly_actions (
    id integer NOT NULL,
    anomaly_id character varying(200) NOT NULL,
    action character varying(50) NOT NULL,
    action_by character varying(100) NOT NULL,
    action_at timestamp with time zone DEFAULT now(),
    notes text
);
--
-- Name: plasticity_anomaly_actions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plasticity_anomaly_actions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: plasticity_anomaly_actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plasticity_anomaly_actions_id_seq OWNED BY public.plasticity_anomaly_actions.id;
--
-- Name: plasticity_observer_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plasticity_observer_log (
    id integer NOT NULL,
    generated_at timestamp with time zone DEFAULT now() NOT NULL,
    overall_health character varying(20) NOT NULL,
    health_score double precision NOT NULL,
    consumers_analyzed integer NOT NULL,
    parameters_tracked integer NOT NULL,
    adjustments_24h integer NOT NULL,
    adjustments_7d integer NOT NULL,
    anomalies_count integer NOT NULL,
    report_json jsonb NOT NULL
);
--
-- Name: plasticity_observer_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plasticity_observer_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: plasticity_observer_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plasticity_observer_log_id_seq OWNED BY public.plasticity_observer_log.id;
--
-- Name: plasticity_outcomes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plasticity_outcomes (
    id integer NOT NULL,
    decision_event_id text NOT NULL,
    outcome_type text NOT NULL,
    outcome_value double precision NOT NULL,
    outcome_metadata jsonb,
    consumer_name text NOT NULL,
    parameter_name text,
    parameter_value double precision,
    recorded_at timestamp with time zone DEFAULT now(),
    CONSTRAINT plasticity_outcomes_outcome_value_check CHECK (((outcome_value >= (0.0)::double precision) AND (outcome_value <= (1.0)::double precision)))
);
--
-- Name: plasticity_outcomes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plasticity_outcomes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: plasticity_outcomes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plasticity_outcomes_id_seq OWNED BY public.plasticity_outcomes.id;
--
-- Name: plasticity_parameter_locks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plasticity_parameter_locks (
    consumer_name character varying(100) NOT NULL,
    parameter_name character varying(100) NOT NULL,
    locked_at timestamp with time zone DEFAULT now(),
    locked_by character varying(100) NOT NULL,
    reason text
);
--
-- Name: recent_autopilot_activity; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.recent_autopilot_activity AS
 SELECT a.action_id,
    a.user_id,
    a.action_type,
    a.ticker,
    a.quantity,
    a.status,
    a.autonomous_mode,
    a.proposed_at,
    a.executed_at,
    s.autopilot_enabled,
    s.demo_mode
   FROM (public.autopilot_actions a
     JOIN public.user_autopilot_settings s ON (((a.user_id)::text = (s.user_id)::text)))
  WHERE (a.proposed_at > (now() - '7 days'::interval))
  ORDER BY a.proposed_at DESC;
--
-- Name: refactor_ledger_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.refactor_ledger_events (
    id integer NOT NULL,
    batch_id character varying(64) NOT NULL,
    batch_size integer NOT NULL,
    trace_ids text[] NOT NULL,
    files_moved integer DEFAULT 0,
    imports_updated integer DEFAULT 0,
    txid character varying(128),
    anchored_at timestamp without time zone DEFAULT now(),
    metadata jsonb
);
--
-- Name: refactor_ledger_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.refactor_ledger_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: refactor_ledger_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.refactor_ledger_events_id_seq OWNED BY public.refactor_ledger_events.id;
--
-- Name: risk_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.risk_logs (
    id integer NOT NULL,
    user_id text,
    ticker text NOT NULL,
    capital numeric,
    entry_price numeric,
    atr numeric,
    sl_price numeric,
    tp_price numeric,
    rr_ratio numeric,
    position_size numeric,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    raw_output jsonb
);
--
-- Name: risk_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.risk_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: risk_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.risk_logs_id_seq OWNED BY public.risk_logs.id;
--
-- Name: screener_features; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.screener_features (
    run_id bigint NOT NULL,
    ticker text NOT NULL,
    instrument_type text NOT NULL,
    category text,
    momentum_z double precision,
    trend_z double precision,
    vola_z double precision,
    sentiment_z double precision,
    composite_score double precision NOT NULL,
    sentiment_raw double precision,
    sentiment_tag text,
    sentiment_at timestamp without time zone
);
--
-- Name: screener_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.screener_results (
    id bigint NOT NULL,
    asof timestamp with time zone NOT NULL,
    profile text NOT NULL,
    filters jsonb NOT NULL,
    top_k integer NOT NULL,
    ranking jsonb NOT NULL,
    notes jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);
--
-- Name: screener_results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.screener_results_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: screener_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.screener_results_id_seq OWNED BY public.screener_results.id;
--
-- Name: sector_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sector_mappings (
    db_sector character varying(100) NOT NULL,
    gics_sector character varying(100) NOT NULL,
    pattern_weaver_concept character varying(100) NOT NULL,
    aliases text[] NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    multilingual_aliases jsonb DEFAULT '{}'::jsonb
);
--
-- Name: semantic_clusters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.semantic_clusters (
    id integer NOT NULL,
    collection text NOT NULL,
    cluster_label integer NOT NULL,
    keywords text[],
    representative_phrases text[],
    n_points integer,
    centroid_vector double precision[],
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: semantic_clusters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.semantic_clusters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: semantic_clusters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.semantic_clusters_id_seq OWNED BY public.semantic_clusters.id;
--
-- Name: semantic_grounding_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.semantic_grounding_events (
    id integer NOT NULL,
    user_id character varying(64) NOT NULL,
    trace_id character varying(64) NOT NULL,
    query_text text NOT NULL,
    language character varying(8),
    affective_state character varying(32),
    semantic_context json,
    embedding_vector double precision[],
    grounding_confidence double precision,
    phrase_hash character varying(128) NOT NULL,
    phase character varying(32),
    qdrant_synced boolean,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: semantic_grounding_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.semantic_grounding_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: semantic_grounding_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.semantic_grounding_events_id_seq OWNED BY public.semantic_grounding_events.id;
--
-- Name: sentiment_scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sentiment_scores (
    id integer NOT NULL,
    ticker text,
    reddit_score double precision,
    google_score double precision,
    combined_score double precision,
    sentiment_tag text,
    timeframe text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    reddit_titles text,
    google_titles text,
    score double precision,
    positive integer DEFAULT 0,
    neutral integer DEFAULT 0,
    negative integer DEFAULT 0,
    dedupe_key text,
    embedded boolean DEFAULT false
);
--
-- Name: sentiment_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: sentiment_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sentiment_scores_id_seq OWNED BY public.sentiment_scores.id;
--
-- Name: sentinel_failover_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sentinel_failover_events (
    id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    old_master_host character varying(255),
    old_master_port integer,
    new_master_host character varying(255),
    new_master_port integer,
    failover_duration_ms integer,
    quorum_votes integer,
    total_sentinels integer,
    triggered_by character varying(255),
    reason text,
    replicas_reconfigured integer,
    event_metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_event_type CHECK (((event_type)::text = ANY ((ARRAY['failover_start'::character varying, 'failover_end'::character varying, 'sdown'::character varying, 'odown'::character varying, 'switch_master'::character varying])::text[])))
);
--
-- Name: sentinel_failover_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentinel_failover_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: sentinel_failover_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sentinel_failover_events_id_seq OWNED BY public.sentinel_failover_events.id;
--
-- Name: sentinel_failover_metrics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.sentinel_failover_metrics AS
 SELECT count(*) AS total_failovers,
    avg(sentinel_failover_events.failover_duration_ms) AS avg_failover_duration_ms,
    min(sentinel_failover_events.failover_duration_ms) AS min_failover_duration_ms,
    max(sentinel_failover_events.failover_duration_ms) AS max_failover_duration_ms,
    count(*) FILTER (WHERE (sentinel_failover_events.failover_duration_ms < 10000)) AS failovers_under_10s,
    count(*) FILTER (WHERE (sentinel_failover_events.created_at > (CURRENT_TIMESTAMP - '24:00:00'::interval))) AS failovers_last_24h,
    count(*) FILTER (WHERE (sentinel_failover_events.created_at > (CURRENT_TIMESTAMP - '7 days'::interval))) AS failovers_last_7d
   FROM public.sentinel_failover_events
  WHERE ((sentinel_failover_events.event_type)::text = 'failover_end'::text);
--
-- Name: sentinel_recent_failovers; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.sentinel_recent_failovers AS
 SELECT sentinel_failover_events.id,
    sentinel_failover_events.event_type,
    concat(sentinel_failover_events.old_master_host, ':', sentinel_failover_events.old_master_port) AS old_master,
    concat(sentinel_failover_events.new_master_host, ':', sentinel_failover_events.new_master_port) AS new_master,
    sentinel_failover_events.failover_duration_ms,
    concat(sentinel_failover_events.quorum_votes, '/', sentinel_failover_events.total_sentinels) AS quorum,
    sentinel_failover_events.created_at,
    EXTRACT(epoch FROM (CURRENT_TIMESTAMP - (sentinel_failover_events.created_at)::timestamp with time zone)) AS seconds_ago
   FROM public.sentinel_failover_events
  WHERE ((sentinel_failover_events.event_type)::text = 'failover_end'::text)
  ORDER BY sentinel_failover_events.created_at DESC
 LIMIT 20;
--
-- Name: shadow_cash_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shadow_cash_accounts (
    account_id integer NOT NULL,
    user_id text NOT NULL,
    starting_capital numeric(15,2) DEFAULT 20000.00 NOT NULL,
    current_cash numeric(15,2) NOT NULL,
    total_deposits numeric(15,2) DEFAULT 0.00,
    total_withdrawals numeric(15,2) DEFAULT 0.00,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    account_status text DEFAULT 'active'::text,
    imported_from text,
    CONSTRAINT check_positive_cash CHECK ((current_cash >= (0)::numeric))
);
--
-- Name: shadow_cash_accounts_account_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shadow_cash_accounts_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: shadow_cash_accounts_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shadow_cash_accounts_account_id_seq OWNED BY public.shadow_cash_accounts.account_id;
--
-- Name: shadow_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shadow_orders (
    order_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id text NOT NULL,
    ticker text NOT NULL,
    side text NOT NULL,
    order_type text DEFAULT 'market'::text NOT NULL,
    quantity integer NOT NULL,
    fill_price numeric(10,2),
    status text NOT NULL,
    rejection_reason text,
    reason text,
    input_text text,
    slippage numeric(8,4),
    commission numeric(8,2) DEFAULT 0.00,
    market_hours boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    filled_at timestamp with time zone,
    conclave_event_id text,
    vee_narrative text,
    vee_generated_at timestamp with time zone,
    vee_model text DEFAULT 'gpt-4o-mini'::text,
    CONSTRAINT check_positive_quantity CHECK ((quantity > 0)),
    CONSTRAINT check_valid_side CHECK ((side = ANY (ARRAY['buy'::text, 'sell'::text]))),
    CONSTRAINT check_valid_status CHECK ((status = ANY (ARRAY['pending'::text, 'filled'::text, 'rejected'::text, 'canceled'::text])))
);
--
-- Name: shadow_orders_with_vee; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.shadow_orders_with_vee AS
 SELECT shadow_orders.order_id,
    shadow_orders.user_id,
    shadow_orders.ticker,
    shadow_orders.side,
    shadow_orders.quantity,
    shadow_orders.fill_price,
    shadow_orders.status,
    shadow_orders.vee_narrative,
    shadow_orders.vee_generated_at,
    shadow_orders.vee_model,
    shadow_orders.filled_at,
    shadow_orders.created_at,
    EXTRACT(epoch FROM (shadow_orders.vee_generated_at - shadow_orders.filled_at)) AS vee_latency_seconds,
        CASE
            WHEN (shadow_orders.vee_narrative IS NOT NULL) THEN 'yes'::text
            WHEN ((shadow_orders.status = 'filled'::text) AND (shadow_orders.vee_narrative IS NULL)) THEN 'missing'::text
            ELSE 'n/a'::text
        END AS vee_status
   FROM public.shadow_orders
  WHERE (shadow_orders.status = ANY (ARRAY['filled'::text, 'rejected'::text]))
  ORDER BY shadow_orders.filled_at DESC NULLS LAST;
--
-- Name: shadow_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shadow_patterns (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    ticker character varying(10) NOT NULL,
    pattern_type character varying(50) NOT NULL,
    signal_strength numeric(5,2) NOT NULL,
    entry_price numeric(12,4) NOT NULL,
    stop_loss numeric(12,4) NOT NULL,
    take_profit numeric(12,4) NOT NULL,
    risk_reward_ratio numeric(5,2) NOT NULL,
    position_size_pct numeric(5,2) NOT NULL,
    vee_narrative text NOT NULL,
    market_context jsonb NOT NULL,
    orthodox_status character varying(20) NOT NULL,
    confidence numeric(3,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT shadow_patterns_confidence_check CHECK (((confidence >= (0)::numeric) AND (confidence <= (1)::numeric))),
    CONSTRAINT shadow_patterns_orthodox_status_check CHECK (((orthodox_status)::text = ANY ((ARRAY['blessed'::character varying, 'purified'::character varying, 'heretical'::character varying])::text[]))),
    CONSTRAINT shadow_patterns_position_size_pct_check CHECK (((position_size_pct >= (0)::numeric) AND (position_size_pct <= (100)::numeric))),
    CONSTRAINT shadow_patterns_signal_strength_check CHECK (((signal_strength >= (0)::numeric) AND (signal_strength <= (10)::numeric)))
);
--
-- Name: shadow_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shadow_patterns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: shadow_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shadow_patterns_id_seq OWNED BY public.shadow_patterns.id;
--
-- Name: shadow_portfolio_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shadow_portfolio_snapshots (
    snapshot_id integer NOT NULL,
    user_id text NOT NULL,
    snapshot_date date DEFAULT CURRENT_DATE NOT NULL,
    total_value numeric(15,2) NOT NULL,
    cash_balance numeric(15,2) NOT NULL,
    positions_value numeric(15,2) NOT NULL,
    daily_pnl numeric(15,2),
    daily_pnl_pct numeric(8,4),
    total_pnl numeric(15,2),
    total_pnl_pct numeric(8,4),
    num_positions integer,
    max_position_pct numeric(5,2),
    created_at timestamp with time zone DEFAULT now(),
    portfolio_data jsonb,
    cash_available numeric(15,2),
    holdings jsonb,
    sector_breakdown jsonb,
    risk_metrics jsonb,
    performance_metrics jsonb,
    construction_rationale text,
    is_demo_mode boolean DEFAULT false
);
--
-- Name: shadow_portfolio_snapshots_snapshot_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shadow_portfolio_snapshots_snapshot_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: shadow_portfolio_snapshots_snapshot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shadow_portfolio_snapshots_snapshot_id_seq OWNED BY public.shadow_portfolio_snapshots.snapshot_id;
--
-- Name: shadow_positions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shadow_positions (
    position_id integer NOT NULL,
    user_id text NOT NULL,
    ticker text NOT NULL,
    quantity integer NOT NULL,
    cost_basis numeric(10,2) NOT NULL,
    total_cost numeric(15,2) NOT NULL,
    market_value numeric(15,2),
    unrealized_pnl numeric(15,2),
    unrealized_pnl_pct numeric(8,4),
    first_purchase_date timestamp with time zone,
    last_updated timestamp with time zone DEFAULT now(),
    CONSTRAINT check_positive_quantity CHECK ((quantity > 0))
);
--
-- Name: shadow_portfolio_summary; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.shadow_portfolio_summary AS
 SELECT ca.user_id,
    ca.current_cash,
    COALESCE(sum(p.market_value), (0)::numeric) AS positions_value,
    (ca.current_cash + COALESCE(sum(p.market_value), (0)::numeric)) AS total_value,
    count(p.position_id) AS num_positions,
    COALESCE(sum(p.unrealized_pnl), (0)::numeric) AS unrealized_pnl,
    ((ca.current_cash + COALESCE(sum(p.market_value), (0)::numeric)) - ca.starting_capital) AS total_pnl,
    ((((ca.current_cash + COALESCE(sum(p.market_value), (0)::numeric)) - ca.starting_capital) / ca.starting_capital) * (100)::numeric) AS total_pnl_pct
   FROM (public.shadow_cash_accounts ca
     LEFT JOIN public.shadow_positions p ON ((ca.user_id = p.user_id)))
  GROUP BY ca.user_id, ca.current_cash, ca.starting_capital;
--
-- Name: shadow_positions_position_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shadow_positions_position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: shadow_positions_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shadow_positions_position_id_seq OWNED BY public.shadow_positions.position_id;
--
-- Name: shadow_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shadow_transactions (
    transaction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id text NOT NULL,
    ticker text NOT NULL,
    transaction_type text NOT NULL,
    quantity integer NOT NULL,
    price numeric(10,2) NOT NULL,
    total_value numeric(15,2) NOT NULL,
    realized_pnl numeric(15,2),
    commission numeric(8,2) DEFAULT 0.00,
    transaction_date timestamp with time zone DEFAULT now(),
    order_id uuid,
    conclave_event_id text,
    CONSTRAINT check_valid_transaction_type CHECK ((transaction_type = ANY (ARRAY['buy'::text, 'sell'::text])))
);
--
-- Name: shadow_recent_transactions; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.shadow_recent_transactions AS
 SELECT t.transaction_id,
    t.user_id,
    t.ticker,
    t.transaction_type,
    t.quantity,
    t.price,
    t.total_value,
    t.realized_pnl,
    t.transaction_date,
    o.reason AS order_reason
   FROM (public.shadow_transactions t
     LEFT JOIN public.shadow_orders o ON ((t.order_id = o.order_id)))
  ORDER BY t.transaction_date DESC;
--
-- Name: shadow_trades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shadow_trades (
    id bigint NOT NULL,
    ticker character varying(20) NOT NULL,
    pattern_type character varying(50) NOT NULL,
    signal_strength numeric(4,2) NOT NULL,
    confidence numeric(3,2) NOT NULL,
    entry_price numeric(12,4) NOT NULL,
    stop_loss numeric(12,4) NOT NULL,
    take_profit numeric(12,4) NOT NULL,
    risk_reward_ratio numeric(5,2) NOT NULL,
    position_size_pct numeric(5,2) DEFAULT 0,
    orthodox_status character varying(20) NOT NULL,
    vee_narrative text NOT NULL,
    vee_generated_by character varying(50) DEFAULT 'gpt-4o-mini'::character varying,
    vee_generation_cost_usd numeric(10,8) DEFAULT 0,
    timeframe character varying(10) NOT NULL,
    data_points integer NOT NULL,
    analysis_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    user_id character varying(255) NOT NULL,
    market_context jsonb,
    technical_indicators jsonb,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT shadow_trades_confidence_check CHECK (((confidence >= (0)::numeric) AND (confidence <= (1)::numeric))),
    CONSTRAINT shadow_trades_orthodox_status_check CHECK (((orthodox_status)::text = ANY ((ARRAY['blessed'::character varying, 'purified'::character varying, 'heretical'::character varying])::text[]))),
    CONSTRAINT shadow_trades_pattern_type_check CHECK (((pattern_type)::text = ANY ((ARRAY['momentum'::character varying, 'reversal'::character varying, 'breakout'::character varying])::text[]))),
    CONSTRAINT shadow_trades_signal_strength_check CHECK (((signal_strength >= (0)::numeric) AND (signal_strength <= (10)::numeric)))
);
--
-- Name: shadow_trades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shadow_trades_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: shadow_trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shadow_trades_id_seq OWNED BY public.shadow_trades.id;
--
-- Name: signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.signals (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    pattern character varying(50),
    confidence double precision,
    source character varying(50),
    timeframe character varying(10),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: signals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.signals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: signals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.signals_id_seq OWNED BY public.signals.id;
--
-- Name: strategies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.strategies (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    trend_short character varying(10),
    trend_mid character varying(10),
    trend_long character varying(10),
    roc_value double precision,
    roc_trend character varying(10),
    macd_value double precision,
    macd_trend character varying(10),
    atr double precision,
    atr_trend character varying(20),
    bandwidth double precision,
    bandwidth_trend character varying(30),
    sentiment_label character varying(10),
    sentiment_score double precision,
    backtest_total_return double precision,
    backtest_annualized double precision,
    backtest_drawdown double precision,
    final_decision character varying(10),
    explanation text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: strategies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.strategies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: strategies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.strategies_id_seq OWNED BY public.strategies.id;
--
-- Name: ticker_metadata; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ticker_metadata (
    ticker character varying(10) NOT NULL,
    company_name character varying(255) NOT NULL,
    sector character varying(100),
    industry character varying(100),
    market_cap numeric(20,2),
    exchange character varying(10),
    is_active boolean DEFAULT true,
    listing_date date,
    delisting_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: tickers_import; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tickers_import (
    ticker text NOT NULL,
    company_name text,
    type public.asset_type,
    isin text,
    exchange text,
    mic text,
    currency text,
    domicile text,
    ter_bps integer,
    distributing boolean,
    replication public.replication_type,
    esg_label boolean,
    fund_category text,
    benchmark text,
    provider text,
    srri smallint,
    active boolean
);
--
-- Name: trend_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trend_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: trend_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trend_logs_id_seq OWNED BY public.trend_logs.id;
--
-- Name: user_analysis_timeline; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_analysis_timeline (
    id integer NOT NULL,
    user_id text NOT NULL,
    tickers text[] NOT NULL,
    company_names text[],
    intent text,
    horizon text,
    route text,
    composite_scores jsonb,
    summary text,
    full_state jsonb,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: user_analysis_timeline_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_analysis_timeline_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: user_analysis_timeline_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_analysis_timeline_id_seq OWNED BY public.user_analysis_timeline.id;
--
-- Name: user_holdings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_holdings (
    id integer NOT NULL,
    user_id text NOT NULL,
    ticker text NOT NULL,
    quantity numeric NOT NULL,
    avg_price numeric NOT NULL,
    current_price numeric,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    company_name text
);
--
-- Name: user_holdings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_holdings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: user_holdings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_holdings_id_seq OWNED BY public.user_holdings.id;
--
-- Name: user_portfolios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_portfolios (
    id integer NOT NULL,
    user_id character varying(100) NOT NULL,
    ticker character varying(10) NOT NULL,
    shares numeric(15,4) NOT NULL,
    purchase_price numeric(15,4),
    purchase_date date,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);
--
-- Name: user_portfolios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_portfolios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: user_portfolios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_portfolios_id_seq OWNED BY public.user_portfolios.id;
--
-- Name: user_subscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_subscriptions (
    user_id text NOT NULL,
    email text,
    tier text DEFAULT 'free'::text NOT NULL,
    started_at timestamp without time zone DEFAULT now(),
    expires_at timestamp without time zone,
    trial_ends_at timestamp without time zone,
    stripe_customer_id text,
    stripe_subscription_id text,
    keycloak_id text,
    features jsonb DEFAULT '{"charts_enabled": true, "export_enabled": false, "timeline_limit": 0, "neural_engine_calls_per_day": 10}'::jsonb,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);
--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id text NOT NULL,
    name text,
    email text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: v_momentum_latest_medium; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_momentum_latest_medium AS
 WITH m AS (
         SELECT momentum_logs.ticker,
                CASE
                    WHEN (momentum_logs.horizon = ANY (ARRAY['medio'::text, 'medium'::text])) THEN 'medium'::text
                    ELSE momentum_logs.horizon
                END AS horizon_norm,
            momentum_logs.rsi,
            momentum_logs.signal,
            momentum_logs."timestamp",
            row_number() OVER (PARTITION BY momentum_logs.ticker ORDER BY momentum_logs."timestamp" DESC) AS rn
           FROM public.momentum_logs
          WHERE (momentum_logs.horizon = ANY (ARRAY['medio'::text, 'medium'::text]))
        )
 SELECT m.ticker,
    m.horizon_norm AS horizon,
    m.rsi,
    m.signal,
    m."timestamp"
   FROM m
  WHERE (m.rn = 1);
--
-- Name: v_ne_last_run_features; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_ne_last_run_features AS
 WITH last AS (
         SELECT screener_results.id
           FROM public.screener_results
          ORDER BY screener_results.id DESC
         LIMIT 1
        )
 SELECT f.run_id,
    f.ticker,
    f.instrument_type,
    f.category,
    f.composite_score,
    f.momentum_z,
    f.trend_z,
    f.vola_z,
    f.sentiment_z
   FROM (public.screener_features f
     JOIN last l ON ((f.run_id = l.id)));
--
-- Name: v_ne_last_run_ranking; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_ne_last_run_ranking AS
 WITH last AS (
         SELECT screener_results.id,
            screener_results.ranking
           FROM public.screener_results
          ORDER BY screener_results.id DESC
         LIMIT 1
        ), stocks AS (
         SELECT (t.elem ->> 'ticker'::text) AS ticker,
            (t.ord)::integer AS rank
           FROM last,
            LATERAL jsonb_array_elements((last.ranking -> 'stocks'::text)) WITH ORDINALITY t(elem, ord)
        )
 SELECT s.rank,
    f.ticker,
    f.instrument_type,
    f.category,
    f.composite_score,
    f.momentum_z,
    f.trend_z,
    f.vola_z,
    f.sentiment_z
   FROM (stocks s
     JOIN public.v_ne_last_run_features f USING (ticker))
  ORDER BY s.rank;
--
-- Name: volatility_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.volatility_logs (
    id integer NOT NULL,
    user_id text,
    ticker text,
    atr numeric,
    signal text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    raw_output jsonb,
    horizon text,
    stdev numeric,
    summary text
);
--
-- Name: v_volatility_latest_medium; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_volatility_latest_medium AS
 WITH v AS (
         SELECT volatility_logs.ticker,
                CASE
                    WHEN (volatility_logs.horizon = ANY (ARRAY['medio'::text, 'medium'::text])) THEN 'medium'::text
                    ELSE volatility_logs.horizon
                END AS horizon_norm,
            volatility_logs.atr,
            volatility_logs.stdev,
            volatility_logs.signal,
            volatility_logs."timestamp",
            row_number() OVER (PARTITION BY volatility_logs.ticker ORDER BY volatility_logs."timestamp" DESC) AS rn
           FROM public.volatility_logs
          WHERE (volatility_logs.horizon = ANY (ARRAY['medio'::text, 'medium'::text]))
        )
 SELECT v.ticker,
    v.horizon_norm AS horizon,
    v.atr,
    v.stdev,
    v.signal,
    v."timestamp"
   FROM v
  WHERE (v.rn = 1);
--
-- Name: validations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.validations (
    id integer NOT NULL,
    ticker text,
    decision text,
    open numeric,
    close numeric,
    change_pct numeric,
    outcome text,
    validation_date date DEFAULT CURRENT_DATE
);
--
-- Name: validations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.validations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: validations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.validations_id_seq OWNED BY public.validations.id;
--
-- Name: vare_adaptations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vare_adaptations (
    id integer NOT NULL,
    parameter character varying(50) NOT NULL,
    old_value numeric(20,6) NOT NULL,
    new_value numeric(20,6) NOT NULL,
    delta numeric(20,6) NOT NULL,
    reason text NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: vare_adaptations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vare_adaptations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vare_adaptations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vare_adaptations_id_seq OWNED BY public.vare_adaptations.id;
--
-- Name: vare_risk_analysis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vare_risk_analysis (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    market_risk double precision NOT NULL,
    volatility_risk double precision NOT NULL,
    liquidity_risk double precision NOT NULL,
    correlation_risk double precision NOT NULL,
    overall_risk double precision NOT NULL,
    risk_category character varying(20) NOT NULL,
    confidence double precision DEFAULT 0.0,
    risk_factors jsonb,
    explanation jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: vare_risk_analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vare_risk_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vare_risk_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vare_risk_analysis_id_seq OWNED BY public.vare_risk_analysis.id;
--
-- Name: vare_risk_scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vare_risk_scores (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    risk_score double precision NOT NULL,
    risk_category character varying(20) NOT NULL,
    confidence double precision,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: vare_risk_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vare_risk_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vare_risk_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vare_risk_scores_id_seq OWNED BY public.vare_risk_scores.id;
--
-- Name: vault_delivery_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_delivery_jobs (
    id integer NOT NULL,
    job_id character varying(255) NOT NULL,
    backup_path text NOT NULL,
    destination_channels text[],
    metadata jsonb,
    priority character varying(20) DEFAULT 'medium'::character varying,
    status character varying(20) DEFAULT 'queued'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    attempts integer DEFAULT 0,
    last_error text
);
--
-- Name: vault_delivery_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_delivery_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_delivery_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_delivery_jobs_id_seq OWNED BY public.vault_delivery_jobs.id;
--
-- Name: vault_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_events (
    id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    keeper character varying(50) NOT NULL,
    payload jsonb,
    context jsonb,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fortress_id character varying(255),
    processed_at timestamp without time zone
);
--
-- Name: vault_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_events_id_seq OWNED BY public.vault_events.id;
--
-- Name: vault_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_history (
    id integer NOT NULL,
    operation character varying(50) NOT NULL,
    keeper character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    details jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone
);
--
-- Name: vault_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_history_id_seq OWNED BY public.vault_history.id;
--
-- Name: vault_keepers_backups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_keepers_backups (
    id integer NOT NULL,
    backup_id character varying(255) NOT NULL,
    backup_type character varying(50) NOT NULL,
    file_path text NOT NULL,
    file_size bigint,
    backup_hash character varying(64),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    metadata jsonb
);
--
-- Name: vault_keepers_backups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_keepers_backups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_keepers_backups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_keepers_backups_id_seq OWNED BY public.vault_keepers_backups.id;
--
-- Name: vault_keepers_delivery_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_keepers_delivery_jobs (
    id integer NOT NULL,
    job_id character varying(255) NOT NULL,
    backup_id character varying(255) NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    total_artifacts integer DEFAULT 0,
    successful_deliveries integer DEFAULT 0,
    failed_deliveries integer DEFAULT 0,
    duration_seconds numeric(10,3),
    delivery_results jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    CONSTRAINT vault_keepers_delivery_jobs_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::text[])))
);
--
-- Name: vault_keepers_delivery_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_keepers_delivery_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_keepers_delivery_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_keepers_delivery_jobs_id_seq OWNED BY public.vault_keepers_delivery_jobs.id;
--
-- Name: vault_keepers_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_keepers_events (
    id integer NOT NULL,
    event_type character varying(100) NOT NULL,
    event_source character varying(100) NOT NULL,
    event_data jsonb NOT NULL,
    priority integer DEFAULT 1,
    processed boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp without time zone,
    CONSTRAINT vault_keepers_events_priority_check CHECK (((priority >= 0) AND (priority <= 5)))
);
--
-- Name: vault_keepers_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_keepers_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_keepers_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_keepers_events_id_seq OWNED BY public.vault_keepers_events.id;
--
-- Name: vault_keepers_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_keepers_history (
    id integer NOT NULL,
    backup_id character varying(255) NOT NULL,
    backup_type character varying(50) NOT NULL,
    status character varying(50) DEFAULT 'started'::character varying NOT NULL,
    trigger_data jsonb,
    result jsonb,
    error_message text,
    size_bytes bigint DEFAULT 0,
    artifacts_count integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    CONSTRAINT vault_keepers_history_backup_type_check CHECK (((backup_type)::text = ANY ((ARRAY['incremental'::character varying, 'critical'::character varying, 'full_system'::character varying, 'disaster_recovery'::character varying])::text[]))),
    CONSTRAINT vault_keepers_history_status_check CHECK (((status)::text = ANY ((ARRAY['started'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying, 'cleaned'::character varying])::text[])))
);
--
-- Name: vault_keepers_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_keepers_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_keepers_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_keepers_history_id_seq OWNED BY public.vault_keepers_history.id;
--
-- Name: vault_keepers_workflows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vault_keepers_workflows (
    id integer NOT NULL,
    workflow_id character varying(255) NOT NULL,
    trigger_source character varying(100) NOT NULL,
    priority integer NOT NULL,
    status character varying(50) DEFAULT 'initialized'::character varying NOT NULL,
    successful_phases integer DEFAULT 0,
    total_phases integer DEFAULT 0,
    duration_seconds numeric(10,3),
    phase_results jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    CONSTRAINT vault_keepers_workflows_priority_check CHECK (((priority >= 1) AND (priority <= 5))),
    CONSTRAINT vault_keepers_workflows_status_check CHECK (((status)::text = ANY ((ARRAY['initialized'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::text[])))
);
--
-- Name: vault_keepers_workflows_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vault_keepers_workflows_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vault_keepers_workflows_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vault_keepers_workflows_id_seq OWNED BY public.vault_keepers_workflows.id;
--
-- Name: vee_explanations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vee_explanations (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    summary text NOT NULL,
    technical text NOT NULL,
    detailed text NOT NULL,
    language character varying(5) DEFAULT 'it'::character varying,
    confidence_level double precision DEFAULT 0.0,
    dominant_factor character varying(100),
    sentiment_direction character varying(20),
    kpi_count integer DEFAULT 0,
    overall_intensity double precision DEFAULT 0.0,
    analysis_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: vee_explanations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vee_explanations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vee_explanations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vee_explanations_id_seq OWNED BY public.vee_explanations.id;
--
-- Name: vhsw_strength_analysis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vhsw_strength_analysis (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    momentum_score double precision NOT NULL,
    stability_score double precision NOT NULL,
    volatility_score double precision NOT NULL,
    trend_strength double precision NOT NULL,
    confidence double precision DEFAULT 0.0,
    windows_analyzed jsonb,
    explanation jsonb,
    technical_details jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: vhsw_strength_analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vhsw_strength_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vhsw_strength_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vhsw_strength_analysis_id_seq OWNED BY public.vhsw_strength_analysis.id;
--
-- Name: vmfl_factor_analysis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vmfl_factor_analysis (
    id integer NOT NULL,
    ticker character varying(10) NOT NULL,
    technical_score double precision NOT NULL,
    fundamental_score double precision NOT NULL,
    sentiment_score double precision NOT NULL,
    momentum_score double precision NOT NULL,
    composite_score double precision NOT NULL,
    strength_category character varying(20) NOT NULL,
    confidence double precision DEFAULT 0.0,
    factor_weights jsonb,
    factor_details jsonb,
    pattern_signals jsonb,
    explanation jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
--
-- Name: vmfl_factor_analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vmfl_factor_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: vmfl_factor_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vmfl_factor_analysis_id_seq OWNED BY public.vmfl_factor_analysis.id;
--
-- Name: volatility_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.volatility_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: volatility_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.volatility_logs_id_seq OWNED BY public.volatility_logs.id;
--
-- Name: weaver_queries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weaver_queries (
    id integer NOT NULL,
    user_id text NOT NULL,
    query_text text NOT NULL,
    concepts jsonb,
    patterns jsonb,
    latency_ms double precision,
    created_at timestamp without time zone DEFAULT now()
);
--
-- Name: weaver_queries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weaver_queries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
--
-- Name: weaver_queries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weaver_queries_id_seq OWNED BY public.weaver_queries.id;
--
-- Name: allocation_results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allocation_results ALTER COLUMN id SET DEFAULT nextval('public.allocation_results_id_seq'::regclass);
--
-- Name: audit_findings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_findings ALTER COLUMN id SET DEFAULT nextval('public.audit_findings_id_seq'::regclass);
--
-- Name: audit_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_sessions ALTER COLUMN id SET DEFAULT nextval('public.audit_sessions_id_seq'::regclass);
--
-- Name: autopilot_actions action_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.autopilot_actions ALTER COLUMN action_id SET DEFAULT nextval('public.autopilot_actions_action_id_seq'::regclass);
--
-- Name: babel_analysis_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.babel_analysis_log ALTER COLUMN id SET DEFAULT nextval('public.babel_analysis_log_id_seq'::regclass);
--
-- Name: backtest_results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_results ALTER COLUMN id SET DEFAULT nextval('public.backtest_results_id_seq'::regclass);
--
-- Name: block_trades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_trades ALTER COLUMN id SET DEFAULT nextval('public.block_trades_id_seq'::regclass);
--
-- Name: coherence_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coherence_logs ALTER COLUMN id SET DEFAULT nextval('public.coherence_logs_id_seq'::regclass);
--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);
--
-- Name: conversations_archive id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations_archive ALTER COLUMN id SET DEFAULT nextval('public.conversations_archive_id_seq'::regclass);
--
-- Name: daily_prices id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_prices ALTER COLUMN id SET DEFAULT nextval('public.daily_prices_id_seq'::regclass);
--
-- Name: dark_pool_volume id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dark_pool_volume ALTER COLUMN id SET DEFAULT nextval('public.dark_pool_volume_id_seq'::regclass);
--
-- Name: dependency_scans id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dependency_scans ALTER COLUMN id SET DEFAULT nextval('public.dependency_scans_id_seq'::regclass);
--
-- Name: design_points id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.design_points ALTER COLUMN id SET DEFAULT nextval('public.design_points_id_seq'::regclass);
--
-- Name: docs_archive id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.docs_archive ALTER COLUMN id SET DEFAULT nextval('public.docs_archive_id_seq'::regclass);
--
-- Name: earnings_calendar id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earnings_calendar ALTER COLUMN id SET DEFAULT nextval('public.earnings_calendar_id_seq'::regclass);
--
-- Name: expedition_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expedition_log ALTER COLUMN id SET DEFAULT nextval('public.expedition_log_id_seq'::regclass);
--
-- Name: explanations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.explanations ALTER COLUMN id SET DEFAULT nextval('public.explanations_id_seq'::regclass);
--
-- Name: factor_explanations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.factor_explanations ALTER COLUMN id SET DEFAULT nextval('public.factor_explanations_id_seq'::regclass);
--
-- Name: factor_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.factor_scores ALTER COLUMN id SET DEFAULT nextval('public.factor_scores_id_seq'::regclass);
--
-- Name: fundamentals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fundamentals ALTER COLUMN id SET DEFAULT nextval('public.fundamentals_id_seq'::regclass);
--
-- Name: gemma_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gemma_logs ALTER COLUMN id SET DEFAULT nextval('public.gemma_logs_id_seq'::regclass);
--
-- Name: guardian_insights insight_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_insights ALTER COLUMN insight_id SET DEFAULT nextval('public.guardian_insights_insight_id_seq'::regclass);
--
-- Name: ledger_anchors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ledger_anchors ALTER COLUMN id SET DEFAULT nextval('public.ledger_anchors_id_seq'::regclass);
--
-- Name: log_agent id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log_agent ALTER COLUMN id SET DEFAULT nextval('public.log_agent_id_seq'::regclass);
--
-- Name: macro_outlook id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macro_outlook ALTER COLUMN id SET DEFAULT nextval('public.macro_outlook_id_seq'::regclass);
--
-- Name: memory_sync_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_sync_logs ALTER COLUMN id SET DEFAULT nextval('public.memory_sync_logs_id_seq'::regclass);
--
-- Name: momentum_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.momentum_logs ALTER COLUMN id SET DEFAULT nextval('public.momentum_logs_id_seq'::regclass);
--
-- Name: options_flow id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.options_flow ALTER COLUMN id SET DEFAULT nextval('public.options_flow_id_seq'::regclass);
--
-- Name: perception_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.perception_logs ALTER COLUMN id SET DEFAULT nextval('public.perception_logs_id_seq'::regclass);
--
-- Name: phrases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrases ALTER COLUMN id SET DEFAULT nextval('public.phrases_id_seq'::regclass);
--
-- Name: plasticity_adjustments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_adjustments ALTER COLUMN id SET DEFAULT nextval('public.plasticity_adjustments_id_seq'::regclass);
--
-- Name: plasticity_anomalies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_anomalies ALTER COLUMN id SET DEFAULT nextval('public.plasticity_anomalies_id_seq'::regclass);
--
-- Name: plasticity_anomaly_actions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_anomaly_actions ALTER COLUMN id SET DEFAULT nextval('public.plasticity_anomaly_actions_id_seq'::regclass);
--
-- Name: plasticity_observer_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_observer_log ALTER COLUMN id SET DEFAULT nextval('public.plasticity_observer_log_id_seq'::regclass);
--
-- Name: plasticity_outcomes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_outcomes ALTER COLUMN id SET DEFAULT nextval('public.plasticity_outcomes_id_seq'::regclass);
--
-- Name: refactor_ledger_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refactor_ledger_events ALTER COLUMN id SET DEFAULT nextval('public.refactor_ledger_events_id_seq'::regclass);
--
-- Name: risk_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_logs ALTER COLUMN id SET DEFAULT nextval('public.risk_logs_id_seq'::regclass);
--
-- Name: screener_results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screener_results ALTER COLUMN id SET DEFAULT nextval('public.screener_results_id_seq'::regclass);
--
-- Name: semantic_clusters id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_clusters ALTER COLUMN id SET DEFAULT nextval('public.semantic_clusters_id_seq'::regclass);
--
-- Name: semantic_grounding_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_grounding_events ALTER COLUMN id SET DEFAULT nextval('public.semantic_grounding_events_id_seq'::regclass);
--
-- Name: sentiment_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiment_scores ALTER COLUMN id SET DEFAULT nextval('public.sentiment_scores_id_seq'::regclass);
--
-- Name: sentinel_failover_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentinel_failover_events ALTER COLUMN id SET DEFAULT nextval('public.sentinel_failover_events_id_seq'::regclass);
--
-- Name: shadow_cash_accounts account_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_cash_accounts ALTER COLUMN account_id SET DEFAULT nextval('public.shadow_cash_accounts_account_id_seq'::regclass);
--
-- Name: shadow_patterns id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_patterns ALTER COLUMN id SET DEFAULT nextval('public.shadow_patterns_id_seq'::regclass);
--
-- Name: shadow_portfolio_snapshots snapshot_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_portfolio_snapshots ALTER COLUMN snapshot_id SET DEFAULT nextval('public.shadow_portfolio_snapshots_snapshot_id_seq'::regclass);
--
-- Name: shadow_positions position_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_positions ALTER COLUMN position_id SET DEFAULT nextval('public.shadow_positions_position_id_seq'::regclass);
--
-- Name: shadow_trades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_trades ALTER COLUMN id SET DEFAULT nextval('public.shadow_trades_id_seq'::regclass);
--
-- Name: signals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signals ALTER COLUMN id SET DEFAULT nextval('public.signals_id_seq'::regclass);
--
-- Name: strategies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategies ALTER COLUMN id SET DEFAULT nextval('public.strategies_id_seq'::regclass);
--
-- Name: trend_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trend_logs ALTER COLUMN id SET DEFAULT nextval('public.trend_logs_id_seq'::regclass);
--
-- Name: user_analysis_timeline id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_analysis_timeline ALTER COLUMN id SET DEFAULT nextval('public.user_analysis_timeline_id_seq'::regclass);
--
-- Name: user_holdings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_holdings ALTER COLUMN id SET DEFAULT nextval('public.user_holdings_id_seq'::regclass);
--
-- Name: user_portfolios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_portfolios ALTER COLUMN id SET DEFAULT nextval('public.user_portfolios_id_seq'::regclass);
--
-- Name: validations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validations ALTER COLUMN id SET DEFAULT nextval('public.validations_id_seq'::regclass);
--
-- Name: vare_adaptations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vare_adaptations ALTER COLUMN id SET DEFAULT nextval('public.vare_adaptations_id_seq'::regclass);
--
-- Name: vare_risk_analysis id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vare_risk_analysis ALTER COLUMN id SET DEFAULT nextval('public.vare_risk_analysis_id_seq'::regclass);
--
-- Name: vare_risk_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vare_risk_scores ALTER COLUMN id SET DEFAULT nextval('public.vare_risk_scores_id_seq'::regclass);
--
-- Name: vault_audit_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_audit_history ALTER COLUMN id SET DEFAULT nextval('public.audit_history_id_seq'::regclass);
--
-- Name: vault_backup_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_backup_history ALTER COLUMN id SET DEFAULT nextval('public.backup_history_id_seq'::regclass);
--
-- Name: vault_delivery_jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_delivery_jobs ALTER COLUMN id SET DEFAULT nextval('public.vault_delivery_jobs_id_seq'::regclass);
--
-- Name: vault_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_events ALTER COLUMN id SET DEFAULT nextval('public.vault_events_id_seq'::regclass);
--
-- Name: vault_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_history ALTER COLUMN id SET DEFAULT nextval('public.vault_history_id_seq'::regclass);
--
-- Name: vault_keepers_backups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_backups ALTER COLUMN id SET DEFAULT nextval('public.vault_keepers_backups_id_seq'::regclass);
--
-- Name: vault_keepers_delivery_jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_delivery_jobs ALTER COLUMN id SET DEFAULT nextval('public.vault_keepers_delivery_jobs_id_seq'::regclass);
--
-- Name: vault_keepers_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_events ALTER COLUMN id SET DEFAULT nextval('public.vault_keepers_events_id_seq'::regclass);
--
-- Name: vault_keepers_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_history ALTER COLUMN id SET DEFAULT nextval('public.vault_keepers_history_id_seq'::regclass);
--
-- Name: vault_keepers_workflows id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_workflows ALTER COLUMN id SET DEFAULT nextval('public.vault_keepers_workflows_id_seq'::regclass);
--
-- Name: vee_explanations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vee_explanations ALTER COLUMN id SET DEFAULT nextval('public.vee_explanations_id_seq'::regclass);
--
-- Name: vhsw_strength_analysis id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vhsw_strength_analysis ALTER COLUMN id SET DEFAULT nextval('public.vhsw_strength_analysis_id_seq'::regclass);
--
-- Name: vmfl_factor_analysis id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vmfl_factor_analysis ALTER COLUMN id SET DEFAULT nextval('public.vmfl_factor_analysis_id_seq'::regclass);
--
-- Name: volatility_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.volatility_logs ALTER COLUMN id SET DEFAULT nextval('public.volatility_logs_id_seq'::regclass);
--
-- Name: weaver_queries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weaver_queries ALTER COLUMN id SET DEFAULT nextval('public.weaver_queries_id_seq'::regclass);
--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);
--
-- Name: allocation_results allocation_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allocation_results
    ADD CONSTRAINT allocation_results_pkey PRIMARY KEY (id);
--
-- Name: audit_findings audit_findings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_findings
    ADD CONSTRAINT audit_findings_pkey PRIMARY KEY (id);
--
-- Name: vault_audit_history audit_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_audit_history
    ADD CONSTRAINT audit_history_pkey PRIMARY KEY (id);
--
-- Name: audit_sessions audit_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_sessions
    ADD CONSTRAINT audit_sessions_pkey PRIMARY KEY (id);
--
-- Name: autopilot_actions autopilot_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.autopilot_actions
    ADD CONSTRAINT autopilot_actions_pkey PRIMARY KEY (action_id);
--
-- Name: babel_analysis_log babel_analysis_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.babel_analysis_log
    ADD CONSTRAINT babel_analysis_log_pkey PRIMARY KEY (id);
--
-- Name: backtest_results backtest_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backtest_results
    ADD CONSTRAINT backtest_results_pkey PRIMARY KEY (id);
--
-- Name: vault_backup_history backup_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_backup_history
    ADD CONSTRAINT backup_history_pkey PRIMARY KEY (id);
--
-- Name: block_trades block_trades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_trades
    ADD CONSTRAINT block_trades_pkey PRIMARY KEY (id);
--
-- Name: coherence_logs coherence_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coherence_logs
    ADD CONSTRAINT coherence_logs_pkey PRIMARY KEY (id);
--
-- Name: conversations_archive conversations_archive_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations_archive
    ADD CONSTRAINT conversations_archive_pkey PRIMARY KEY (id);
--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);
--
-- Name: daily_prices daily_prices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.daily_prices
    ADD CONSTRAINT daily_prices_pkey PRIMARY KEY (id);
--
-- Name: dark_pool_volume dark_pool_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dark_pool_volume
    ADD CONSTRAINT dark_pool_unique UNIQUE (ticker, date, source);
--
-- Name: dark_pool_volume dark_pool_volume_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dark_pool_volume
    ADD CONSTRAINT dark_pool_volume_pkey PRIMARY KEY (id);
--
-- Name: dependency_scans dependency_scans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dependency_scans
    ADD CONSTRAINT dependency_scans_pkey PRIMARY KEY (id);
--
-- Name: design_points design_points_designpoint_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.design_points
    ADD CONSTRAINT design_points_designpoint_id_key UNIQUE (designpoint_id);
--
-- Name: design_points design_points_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.design_points
    ADD CONSTRAINT design_points_pkey PRIMARY KEY (id);
--
-- Name: docs_archive docs_archive_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.docs_archive
    ADD CONSTRAINT docs_archive_pkey PRIMARY KEY (id);
--
-- Name: earnings_calendar earnings_calendar_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earnings_calendar
    ADD CONSTRAINT earnings_calendar_pkey PRIMARY KEY (id);
--
-- Name: earnings_calendar earnings_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earnings_calendar
    ADD CONSTRAINT earnings_unique UNIQUE (ticker, earnings_date, fiscal_quarter);
--
-- Name: expedition_log expedition_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expedition_log
    ADD CONSTRAINT expedition_log_pkey PRIMARY KEY (id);
--
-- Name: explanations explanations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.explanations
    ADD CONSTRAINT explanations_pkey PRIMARY KEY (id);
--
-- Name: factor_explanations factor_explanations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.factor_explanations
    ADD CONSTRAINT factor_explanations_pkey PRIMARY KEY (id);
--
-- Name: factor_scores factor_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.factor_scores
    ADD CONSTRAINT factor_scores_pkey PRIMARY KEY (id);
--
-- Name: factor_scores factor_scores_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.factor_scores
    ADD CONSTRAINT factor_scores_unique UNIQUE (ticker, date);
--
-- Name: fundamentals fundamentals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fundamentals
    ADD CONSTRAINT fundamentals_pkey PRIMARY KEY (id);
--
-- Name: fundamentals fundamentals_ticker_date_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fundamentals
    ADD CONSTRAINT fundamentals_ticker_date_unique UNIQUE (ticker, date);
--
-- Name: gemma_logs gemma_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gemma_logs
    ADD CONSTRAINT gemma_logs_pkey PRIMARY KEY (id);
--
-- Name: guardian_insights guardian_insights_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_insights
    ADD CONSTRAINT guardian_insights_pkey PRIMARY KEY (insight_id);
--
-- Name: intake_sessions intake_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intake_sessions
    ADD CONSTRAINT intake_sessions_pkey PRIMARY KEY (session_id);
--
-- Name: langgraph_workflows langgraph_workflows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.langgraph_workflows
    ADD CONSTRAINT langgraph_workflows_pkey PRIMARY KEY (workflow_id);
--
-- Name: ledger_anchors ledger_anchors_blockchain_txid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ledger_anchors
    ADD CONSTRAINT ledger_anchors_blockchain_txid_key UNIQUE (blockchain_txid);
--
-- Name: ledger_anchors ledger_anchors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ledger_anchors
    ADD CONSTRAINT ledger_anchors_pkey PRIMARY KEY (id);
--
-- Name: log_agent log_agent_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log_agent
    ADD CONSTRAINT log_agent_pkey PRIMARY KEY (id);
--
-- Name: macro_outlook macro_outlook_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macro_outlook
    ADD CONSTRAINT macro_outlook_pkey PRIMARY KEY (id);
--
-- Name: macro_outlook macro_outlook_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.macro_outlook
    ADD CONSTRAINT macro_outlook_unique UNIQUE (date, source);
--
-- Name: mcp_tool_calls mcp_tool_calls_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mcp_tool_calls
    ADD CONSTRAINT mcp_tool_calls_pkey PRIMARY KEY (conclave_id);
--
-- Name: memory_sync_logs memory_sync_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_sync_logs
    ADD CONSTRAINT memory_sync_logs_pkey PRIMARY KEY (id);
--
-- Name: momentum_logs momentum_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.momentum_logs
    ADD CONSTRAINT momentum_logs_pkey PRIMARY KEY (id);
--
-- Name: ohlcv_daily ohlcv_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ohlcv_daily
    ADD CONSTRAINT ohlcv_daily_pkey PRIMARY KEY (ticker, dt);
--
-- Name: options_flow options_flow_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.options_flow
    ADD CONSTRAINT options_flow_pkey PRIMARY KEY (id);
--
-- Name: options_flow options_flow_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.options_flow
    ADD CONSTRAINT options_flow_unique UNIQUE (ticker, date, source);
--
-- Name: perception_logs perception_logs_perception_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.perception_logs
    ADD CONSTRAINT perception_logs_perception_id_key UNIQUE (perception_id);
--
-- Name: perception_logs perception_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.perception_logs
    ADD CONSTRAINT perception_logs_pkey PRIMARY KEY (id);
--
-- Name: phrases phrases_phrase_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrases
    ADD CONSTRAINT phrases_phrase_hash_key UNIQUE (phrase_hash);
--
-- Name: phrases phrases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrases
    ADD CONSTRAINT phrases_pkey PRIMARY KEY (id);
--
-- Name: plasticity_adjustments plasticity_adjustments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_adjustments
    ADD CONSTRAINT plasticity_adjustments_pkey PRIMARY KEY (id);
--
-- Name: plasticity_anomalies plasticity_anomalies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_anomalies
    ADD CONSTRAINT plasticity_anomalies_pkey PRIMARY KEY (id);
--
-- Name: plasticity_anomaly_actions plasticity_anomaly_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_anomaly_actions
    ADD CONSTRAINT plasticity_anomaly_actions_pkey PRIMARY KEY (id);
--
-- Name: plasticity_observer_log plasticity_observer_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_observer_log
    ADD CONSTRAINT plasticity_observer_log_pkey PRIMARY KEY (id);
--
-- Name: plasticity_outcomes plasticity_outcomes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_outcomes
    ADD CONSTRAINT plasticity_outcomes_pkey PRIMARY KEY (id);
--
-- Name: plasticity_parameter_locks plasticity_parameter_locks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plasticity_parameter_locks
    ADD CONSTRAINT plasticity_parameter_locks_pkey PRIMARY KEY (consumer_name, parameter_name);
--
-- Name: refactor_ledger_events refactor_ledger_events_batch_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refactor_ledger_events
    ADD CONSTRAINT refactor_ledger_events_batch_id_key UNIQUE (batch_id);
--
-- Name: refactor_ledger_events refactor_ledger_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refactor_ledger_events
    ADD CONSTRAINT refactor_ledger_events_pkey PRIMARY KEY (id);
--
-- Name: risk_logs risk_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_logs
    ADD CONSTRAINT risk_logs_pkey PRIMARY KEY (id);
--
-- Name: screener_features screener_features_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screener_features
    ADD CONSTRAINT screener_features_pkey PRIMARY KEY (run_id, ticker);
--
-- Name: screener_results screener_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screener_results
    ADD CONSTRAINT screener_results_pkey PRIMARY KEY (id);
--
-- Name: sector_mappings sector_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sector_mappings
    ADD CONSTRAINT sector_mappings_pkey PRIMARY KEY (db_sector);
--
-- Name: semantic_clusters semantic_clusters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_clusters
    ADD CONSTRAINT semantic_clusters_pkey PRIMARY KEY (id);
--
-- Name: semantic_grounding_events semantic_grounding_events_phrase_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_grounding_events
    ADD CONSTRAINT semantic_grounding_events_phrase_hash_key UNIQUE (phrase_hash);
--
-- Name: semantic_grounding_events semantic_grounding_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_grounding_events
    ADD CONSTRAINT semantic_grounding_events_pkey PRIMARY KEY (id);
--
-- Name: sentiment_scores sentiment_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiment_scores
    ADD CONSTRAINT sentiment_scores_pkey PRIMARY KEY (id);
--
-- Name: sentinel_failover_events sentinel_failover_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentinel_failover_events
    ADD CONSTRAINT sentinel_failover_events_pkey PRIMARY KEY (id);
--
-- Name: shadow_cash_accounts shadow_cash_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_cash_accounts
    ADD CONSTRAINT shadow_cash_accounts_pkey PRIMARY KEY (account_id);
--
-- Name: shadow_cash_accounts shadow_cash_accounts_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_cash_accounts
    ADD CONSTRAINT shadow_cash_accounts_user_id_key UNIQUE (user_id);
--
-- Name: shadow_orders shadow_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_orders
    ADD CONSTRAINT shadow_orders_pkey PRIMARY KEY (order_id);
--
-- Name: shadow_patterns shadow_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_patterns
    ADD CONSTRAINT shadow_patterns_pkey PRIMARY KEY (id);
--
-- Name: shadow_portfolio_snapshots shadow_portfolio_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_portfolio_snapshots
    ADD CONSTRAINT shadow_portfolio_snapshots_pkey PRIMARY KEY (snapshot_id);
--
-- Name: shadow_positions shadow_positions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_positions
    ADD CONSTRAINT shadow_positions_pkey PRIMARY KEY (position_id);
--
-- Name: shadow_trades shadow_trades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_trades
    ADD CONSTRAINT shadow_trades_pkey PRIMARY KEY (id);
--
-- Name: shadow_transactions shadow_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_transactions
    ADD CONSTRAINT shadow_transactions_pkey PRIMARY KEY (transaction_id);
--
-- Name: signals signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_pkey PRIMARY KEY (id);
--
-- Name: strategies strategies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strategies
    ADD CONSTRAINT strategies_pkey PRIMARY KEY (id);
--
-- Name: ticker_metadata ticker_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ticker_metadata
    ADD CONSTRAINT ticker_metadata_pkey PRIMARY KEY (ticker);
--
-- Name: tickers_import tickers_import_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickers_import
    ADD CONSTRAINT tickers_import_pkey PRIMARY KEY (ticker);
--
-- Name: tickers tickers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickers
    ADD CONSTRAINT tickers_pkey PRIMARY KEY (ticker);
--
-- Name: trend_logs trend_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trend_logs
    ADD CONSTRAINT trend_logs_pkey PRIMARY KEY (id);
--
-- Name: shadow_portfolio_snapshots unique_daily_snapshot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_portfolio_snapshots
    ADD CONSTRAINT unique_daily_snapshot UNIQUE (user_id, snapshot_date);
--
-- Name: phrases unique_phrase_hash; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrases
    ADD CONSTRAINT unique_phrase_hash UNIQUE (phrase_hash);
--
-- Name: shadow_positions unique_shadow_position; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_positions
    ADD CONSTRAINT unique_shadow_position UNIQUE (user_id, ticker);
--
-- Name: user_holdings unique_user_ticker; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_holdings
    ADD CONSTRAINT unique_user_ticker UNIQUE (user_id, ticker);
--
-- Name: user_analysis_timeline user_analysis_timeline_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_analysis_timeline
    ADD CONSTRAINT user_analysis_timeline_pkey PRIMARY KEY (id);
--
-- Name: user_autopilot_settings user_autopilot_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_autopilot_settings
    ADD CONSTRAINT user_autopilot_settings_pkey PRIMARY KEY (user_id);
--
-- Name: user_holdings user_holdings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_holdings
    ADD CONSTRAINT user_holdings_pkey PRIMARY KEY (id);
--
-- Name: user_portfolios user_portfolios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_portfolios
    ADD CONSTRAINT user_portfolios_pkey PRIMARY KEY (id);
--
-- Name: user_portfolios user_portfolios_user_id_ticker_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_portfolios
    ADD CONSTRAINT user_portfolios_user_id_ticker_key UNIQUE (user_id, ticker);
--
-- Name: user_subscriptions user_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_subscriptions
    ADD CONSTRAINT user_subscriptions_pkey PRIMARY KEY (user_id);
--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
--
-- Name: sentiment_scores ux_sentiment_dedupe; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiment_scores
    ADD CONSTRAINT ux_sentiment_dedupe UNIQUE (dedupe_key);
--
-- Name: validations validations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validations
    ADD CONSTRAINT validations_pkey PRIMARY KEY (id);
--
-- Name: vare_adaptations vare_adaptations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vare_adaptations
    ADD CONSTRAINT vare_adaptations_pkey PRIMARY KEY (id);
--
-- Name: vare_risk_analysis vare_risk_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vare_risk_analysis
    ADD CONSTRAINT vare_risk_analysis_pkey PRIMARY KEY (id);
--
-- Name: vare_risk_scores vare_risk_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vare_risk_scores
    ADD CONSTRAINT vare_risk_scores_pkey PRIMARY KEY (id);
--
-- Name: vare_risk_scores vare_risk_scores_ticker_created_at_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vare_risk_scores
    ADD CONSTRAINT vare_risk_scores_ticker_created_at_key UNIQUE (ticker, created_at);
--
-- Name: vault_delivery_jobs vault_delivery_jobs_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_delivery_jobs
    ADD CONSTRAINT vault_delivery_jobs_job_id_key UNIQUE (job_id);
--
-- Name: vault_delivery_jobs vault_delivery_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_delivery_jobs
    ADD CONSTRAINT vault_delivery_jobs_pkey PRIMARY KEY (id);
--
-- Name: vault_events vault_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_events
    ADD CONSTRAINT vault_events_pkey PRIMARY KEY (id);
--
-- Name: vault_history vault_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_history
    ADD CONSTRAINT vault_history_pkey PRIMARY KEY (id);
--
-- Name: vault_keepers_backups vault_keepers_backups_backup_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_backups
    ADD CONSTRAINT vault_keepers_backups_backup_id_key UNIQUE (backup_id);
--
-- Name: vault_keepers_backups vault_keepers_backups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_backups
    ADD CONSTRAINT vault_keepers_backups_pkey PRIMARY KEY (id);
--
-- Name: vault_keepers_delivery_jobs vault_keepers_delivery_jobs_job_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_delivery_jobs
    ADD CONSTRAINT vault_keepers_delivery_jobs_job_id_key UNIQUE (job_id);
--
-- Name: vault_keepers_delivery_jobs vault_keepers_delivery_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_delivery_jobs
    ADD CONSTRAINT vault_keepers_delivery_jobs_pkey PRIMARY KEY (id);
--
-- Name: vault_keepers_events vault_keepers_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_events
    ADD CONSTRAINT vault_keepers_events_pkey PRIMARY KEY (id);
--
-- Name: vault_keepers_history vault_keepers_history_backup_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_history
    ADD CONSTRAINT vault_keepers_history_backup_id_key UNIQUE (backup_id);
--
-- Name: vault_keepers_history vault_keepers_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_history
    ADD CONSTRAINT vault_keepers_history_pkey PRIMARY KEY (id);
--
-- Name: vault_keepers_workflows vault_keepers_workflows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_workflows
    ADD CONSTRAINT vault_keepers_workflows_pkey PRIMARY KEY (id);
--
-- Name: vault_keepers_workflows vault_keepers_workflows_workflow_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vault_keepers_workflows
    ADD CONSTRAINT vault_keepers_workflows_workflow_id_key UNIQUE (workflow_id);
--
-- Name: vee_explanations vee_explanations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vee_explanations
    ADD CONSTRAINT vee_explanations_pkey PRIMARY KEY (id);
--
-- Name: vhsw_strength_analysis vhsw_strength_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vhsw_strength_analysis
    ADD CONSTRAINT vhsw_strength_analysis_pkey PRIMARY KEY (id);
--
-- Name: vmfl_factor_analysis vmfl_factor_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vmfl_factor_analysis
    ADD CONSTRAINT vmfl_factor_analysis_pkey PRIMARY KEY (id);
--
-- Name: volatility_logs volatility_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.volatility_logs
    ADD CONSTRAINT volatility_logs_pkey PRIMARY KEY (id);
--
-- Name: weaver_queries weaver_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weaver_queries
    ADD CONSTRAINT weaver_queries_pkey PRIMARY KEY (id);
--
-- Name: idx_actions_autonomous; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_actions_autonomous ON public.autopilot_actions USING btree (autonomous_mode);
--
-- Name: idx_actions_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_actions_pending ON public.autopilot_actions USING btree (status) WHERE ((status)::text = 'pending'::text);
--
-- Name: idx_actions_proposed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_actions_proposed_at ON public.autopilot_actions USING btree (proposed_at DESC);
--
-- Name: idx_actions_user_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_actions_user_status ON public.autopilot_actions USING btree (user_id, status);
--
-- Name: idx_adjustments_consumer_param; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_adjustments_consumer_param ON public.plasticity_adjustments USING btree (consumer_name, parameter_name, created_at DESC);
--
-- Name: idx_adjustments_manual; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_adjustments_manual ON public.plasticity_adjustments USING btree (is_manual, created_at DESC) WHERE (is_manual = true);
--
-- Name: idx_anomalies_unresolved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_anomalies_unresolved ON public.plasticity_anomalies USING btree (detected_at DESC) WHERE (resolved_at IS NULL);
--
-- Name: idx_anomaly_actions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_anomaly_actions_id ON public.plasticity_anomaly_actions USING btree (anomaly_id);
--
-- Name: idx_audit_findings_ledger_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_findings_ledger_batch ON public.audit_findings USING btree (ledger_batch_id);
--
-- Name: idx_audit_findings_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_findings_session ON public.audit_findings USING btree (audit_session_id);
--
-- Name: idx_audit_findings_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_findings_severity ON public.audit_findings USING btree (severity);
--
-- Name: idx_audit_sessions_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_sessions_created ON public.audit_sessions USING btree (created_at);
--
-- Name: idx_audit_sessions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_sessions_status ON public.audit_sessions USING btree (status);
--
-- Name: idx_audit_sessions_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_sessions_type ON public.audit_sessions USING btree (audit_type);
--
-- Name: idx_autopilot_autonomous; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_autonomous ON public.autopilot_actions USING btree (autonomous_mode);
--
-- Name: idx_autopilot_demo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_demo ON public.autopilot_actions USING btree (is_demo_mode);
--
-- Name: idx_autopilot_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_pending ON public.autopilot_actions USING btree (status) WHERE ((status)::text = 'pending'::text);
--
-- Name: idx_autopilot_proposed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_proposed ON public.autopilot_actions USING btree (proposed_at DESC);
--
-- Name: idx_autopilot_risk; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_risk ON public.autopilot_actions USING btree (risk_score);
--
-- Name: idx_autopilot_settings_autonomous; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_settings_autonomous ON public.user_autopilot_settings USING btree (autonomous_mode);
--
-- Name: idx_autopilot_settings_demo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_settings_demo ON public.user_autopilot_settings USING btree (demo_mode);
--
-- Name: idx_autopilot_user_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_autopilot_user_status ON public.autopilot_actions USING btree (user_id, status);
--
-- Name: idx_babel_log_correlation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_babel_log_correlation_id ON public.babel_analysis_log USING btree (correlation_id);
--
-- Name: idx_babel_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_babel_log_created_at ON public.babel_analysis_log USING btree (created_at);
--
-- Name: idx_babel_log_language; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_babel_log_language ON public.babel_analysis_log USING btree (language_detected);
--
-- Name: idx_babel_log_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_babel_log_user_id ON public.babel_analysis_log USING btree (user_id);
--
-- Name: idx_block_ticker_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_ticker_timestamp ON public.block_trades USING btree (ticker, "timestamp" DESC);
--
-- Name: idx_coherence_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coherence_timestamp ON public.coherence_logs USING btree ("timestamp" DESC);
--
-- Name: idx_conversations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_user_id ON public.conversations USING btree (user_id, created_at DESC);
--
-- Name: idx_daily_prices_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daily_prices_ticker ON public.daily_prices USING btree (ticker);
--
-- Name: idx_daily_prices_ticker_date; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_daily_prices_ticker_date ON public.daily_prices USING btree (ticker, date("timestamp"));
--
-- Name: idx_daily_prices_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daily_prices_timestamp ON public.daily_prices USING btree ("timestamp" DESC);
--
-- Name: idx_dark_pool_ticker_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dark_pool_ticker_date ON public.dark_pool_volume USING btree (ticker, date DESC);
--
-- Name: idx_dependency_scans_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dependency_scans_session ON public.dependency_scans USING btree (audit_session_id);
--
-- Name: idx_design_points_doctrine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_design_points_doctrine ON public.design_points USING btree (doctrine);
--
-- Name: idx_design_points_pareto; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_design_points_pareto ON public.design_points USING btree (is_pareto);
--
-- Name: idx_design_points_scenario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_design_points_scenario ON public.design_points USING btree (scenario_id);
--
-- Name: idx_docs_archive_doc_title; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_docs_archive_doc_title ON public.docs_archive USING btree (doc_title);
--
-- Name: idx_earnings_ticker_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earnings_ticker_date ON public.earnings_calendar USING btree (ticker, earnings_date DESC);
--
-- Name: idx_emergency_stop; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emergency_stop ON public.user_autopilot_settings USING btree (emergency_stop_active);
--
-- Name: idx_explanations_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_explanations_created_at ON public.explanations USING btree (created_at);
--
-- Name: idx_explanations_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_explanations_ticker ON public.explanations USING btree (ticker);
--
-- Name: idx_explanations_ticker_lang; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_explanations_ticker_lang ON public.explanations USING btree (ticker, language);
--
-- Name: idx_explanations_ticker_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_explanations_ticker_time ON public.explanations USING btree (ticker, created_at DESC);
--
-- Name: idx_fundamentals_dividend_yield; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fundamentals_dividend_yield ON public.fundamentals USING btree (dividend_yield DESC) WHERE (dividend_yield IS NOT NULL);
--
-- Name: idx_fundamentals_pe_ratio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fundamentals_pe_ratio ON public.fundamentals USING btree (pe_ratio) WHERE ((pe_ratio IS NOT NULL) AND (pe_ratio > (0)::numeric));
--
-- Name: idx_fundamentals_ticker_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fundamentals_ticker_date ON public.fundamentals USING btree (ticker, date DESC);
--
-- Name: idx_grounding_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grounding_created ON public.semantic_grounding_events USING btree (created_at);
--
-- Name: idx_grounding_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grounding_phase ON public.semantic_grounding_events USING btree (phase);
--
-- Name: idx_grounding_synced; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grounding_synced ON public.semantic_grounding_events USING btree (qdrant_synced);
--
-- Name: idx_grounding_trace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grounding_trace_id ON public.semantic_grounding_events USING btree (trace_id);
--
-- Name: idx_grounding_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_grounding_user_id ON public.semantic_grounding_events USING btree (user_id);
--
-- Name: idx_guardian_demo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_guardian_demo ON public.guardian_insights USING btree (is_demo_mode);
--
-- Name: idx_guardian_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_guardian_pending ON public.guardian_insights USING btree (user_action) WHERE ((user_action)::text = 'pending'::text);
--
-- Name: idx_guardian_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_guardian_severity ON public.guardian_insights USING btree (severity);
--
-- Name: idx_guardian_snapshot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_guardian_snapshot ON public.guardian_insights USING btree (snapshot_id);
--
-- Name: idx_guardian_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_guardian_type ON public.guardian_insights USING btree (insight_type);
--
-- Name: idx_guardian_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_guardian_user_created ON public.guardian_insights USING btree (user_id, created_at DESC);
--
-- Name: idx_insights_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_pending ON public.guardian_insights USING btree (user_action) WHERE ((user_action)::text = 'pending'::text);
--
-- Name: idx_insights_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_severity ON public.guardian_insights USING btree (severity);
--
-- Name: idx_insights_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_type ON public.guardian_insights USING btree (insight_type);
--
-- Name: idx_insights_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_insights_user_created ON public.guardian_insights USING btree (user_id, created_at DESC);
--
-- Name: idx_intake_sessions_phase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intake_sessions_phase ON public.intake_sessions USING btree (can_phase) WHERE ((can_phase)::text = 'intake'::text);
--
-- Name: idx_intake_sessions_state_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intake_sessions_state_gin ON public.intake_sessions USING gin (intake_state);
--
-- Name: idx_intake_sessions_trace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intake_sessions_trace ON public.intake_sessions USING btree (trace_id) WHERE (trace_id IS NOT NULL);
--
-- Name: idx_intake_sessions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intake_sessions_user ON public.intake_sessions USING btree (user_id, updated_at DESC);
--
-- Name: idx_langgraph_workflows_final_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_langgraph_workflows_final_state ON public.langgraph_workflows USING gin (final_state);
--
-- Name: idx_langgraph_workflows_intent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_langgraph_workflows_intent ON public.langgraph_workflows USING btree (intent, created_at DESC);
--
-- Name: idx_langgraph_workflows_route_sequence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_langgraph_workflows_route_sequence ON public.langgraph_workflows USING gin (route_sequence);
--
-- Name: idx_langgraph_workflows_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_langgraph_workflows_user_id ON public.langgraph_workflows USING btree (user_id, created_at DESC);
--
-- Name: idx_ledger_anchors_anchored_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ledger_anchors_anchored_at ON public.ledger_anchors USING btree (anchored_at DESC);
--
-- Name: idx_ledger_anchors_txid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ledger_anchors_txid ON public.ledger_anchors USING btree (blockchain_txid);
--
-- Name: idx_log_agent_agent_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_log_agent_agent_time ON public.log_agent USING btree (agent, created_at DESC);
--
-- Name: idx_log_agent_payload_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_log_agent_payload_gin ON public.log_agent USING gin (payload_json);
--
-- Name: idx_log_agent_ticker_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_log_agent_ticker_time ON public.log_agent USING btree (ticker, created_at DESC);
--
-- Name: idx_log_agent_trace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_log_agent_trace_id ON public.log_agent USING btree (trace_id);
--
-- Name: idx_mcp_tool_calls_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mcp_tool_calls_created_at ON public.mcp_tool_calls USING btree (created_at DESC);
--
-- Name: idx_mcp_tool_calls_orthodoxy_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mcp_tool_calls_orthodoxy_status ON public.mcp_tool_calls USING btree (orthodoxy_status);
--
-- Name: idx_mcp_tool_calls_tool_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mcp_tool_calls_tool_name ON public.mcp_tool_calls USING btree (tool_name);
--
-- Name: idx_mcp_tool_calls_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mcp_tool_calls_user_id ON public.mcp_tool_calls USING btree (user_id);
--
-- Name: idx_memory_sync_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_memory_sync_timestamp ON public.memory_sync_logs USING btree ("timestamp" DESC);
--
-- Name: idx_momentum_ticker_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_momentum_ticker_time ON public.momentum_logs USING btree (ticker, "timestamp" DESC);
--
-- Name: idx_observer_log_generated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_observer_log_generated ON public.plasticity_observer_log USING btree (generated_at DESC);
--
-- Name: idx_ohlcv_ticker_dt; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ohlcv_ticker_dt ON public.ohlcv_daily USING btree (ticker, dt DESC);
--
-- Name: idx_options_ticker_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_options_ticker_date ON public.options_flow USING btree (ticker, date DESC);
--
-- Name: idx_perception_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perception_created_at ON public.perception_logs USING btree (created_at DESC);
--
-- Name: idx_perception_metadata; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perception_metadata ON public.perception_logs USING gin (metadata);
--
-- Name: idx_perception_sensor_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perception_sensor_type ON public.perception_logs USING btree (sensor_type);
--
-- Name: idx_perception_test_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perception_test_id ON public.perception_logs USING btree (test_id);
--
-- Name: idx_perception_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_perception_user_id ON public.perception_logs USING btree (user_id);
--
-- Name: idx_phrases_phrase_text_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrases_phrase_text_gin ON public.phrases USING gin (phrase_text public.gin_trgm_ops);
--
-- Name: idx_phrases_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrases_ticker ON public.phrases USING btree (ticker);
--
-- Name: idx_plasticity_consumer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plasticity_consumer ON public.plasticity_outcomes USING btree (consumer_name, recorded_at DESC);
--
-- Name: idx_plasticity_decision; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plasticity_decision ON public.plasticity_outcomes USING btree (decision_event_id);
--
-- Name: idx_plasticity_parameter; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plasticity_parameter ON public.plasticity_outcomes USING btree (consumer_name, parameter_name, recorded_at DESC);
--
-- Name: idx_plasticity_recorded_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plasticity_recorded_at ON public.plasticity_outcomes USING btree (recorded_at DESC);
--
-- Name: idx_refactor_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refactor_batch_id ON public.refactor_ledger_events USING btree (batch_id);
--
-- Name: idx_refactor_txid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_refactor_txid ON public.refactor_ledger_events USING btree (txid);
--
-- Name: idx_sector_mappings_gics; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sector_mappings_gics ON public.sector_mappings USING btree (gics_sector);
--
-- Name: idx_sector_mappings_pw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sector_mappings_pw ON public.sector_mappings USING btree (pattern_weaver_concept);
--
-- Name: idx_semantic_clusters_collection; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_semantic_clusters_collection ON public.semantic_clusters USING btree (collection);
--
-- Name: idx_sent_ticker_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sent_ticker_time ON public.sentiment_scores USING btree (ticker, created_at DESC);
--
-- Name: idx_sentinel_failover_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sentinel_failover_created ON public.sentinel_failover_events USING btree (created_at DESC);
--
-- Name: idx_sentinel_failover_master; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sentinel_failover_master ON public.sentinel_failover_events USING btree (new_master_host, new_master_port);
--
-- Name: idx_sentinel_failover_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sentinel_failover_type ON public.sentinel_failover_events USING btree (event_type);
--
-- Name: idx_settings_autonomous; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_settings_autonomous ON public.user_autopilot_settings USING btree (autonomous_mode);
--
-- Name: idx_settings_demo_mode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_settings_demo_mode ON public.user_autopilot_settings USING btree (demo_mode);
--
-- Name: idx_sf_composite_desc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sf_composite_desc ON public.screener_features USING btree (composite_score DESC);
--
-- Name: idx_sf_sent_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sf_sent_at ON public.screener_features USING btree (sentiment_at DESC);
--
-- Name: idx_shadow_cash_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_cash_status ON public.shadow_cash_accounts USING btree (account_status);
--
-- Name: idx_shadow_cash_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_cash_user ON public.shadow_cash_accounts USING btree (user_id);
--
-- Name: idx_shadow_orders_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_orders_created ON public.shadow_orders USING btree (created_at DESC);
--
-- Name: idx_shadow_orders_filled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_orders_filled ON public.shadow_orders USING btree (filled_at DESC) WHERE (filled_at IS NOT NULL);
--
-- Name: idx_shadow_orders_has_vee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_orders_has_vee ON public.shadow_orders USING btree (vee_generated_at DESC) WHERE (vee_narrative IS NOT NULL);
--
-- Name: idx_shadow_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_orders_status ON public.shadow_orders USING btree (status);
--
-- Name: idx_shadow_orders_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_orders_ticker ON public.shadow_orders USING btree (ticker);
--
-- Name: idx_shadow_orders_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_orders_user ON public.shadow_orders USING btree (user_id);
--
-- Name: idx_shadow_orders_vee_narrative_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_orders_vee_narrative_gin ON public.shadow_orders USING gin (to_tsvector('english'::regconfig, vee_narrative));
--
-- Name: idx_shadow_patterns_context_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_patterns_context_gin ON public.shadow_patterns USING gin (market_context);
--
-- Name: idx_shadow_patterns_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_patterns_created ON public.shadow_patterns USING btree (created_at DESC);
--
-- Name: idx_shadow_patterns_orthodox; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_patterns_orthodox ON public.shadow_patterns USING btree (orthodox_status);
--
-- Name: idx_shadow_patterns_strength; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_patterns_strength ON public.shadow_patterns USING btree (signal_strength DESC);
--
-- Name: idx_shadow_patterns_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_patterns_ticker ON public.shadow_patterns USING btree (ticker);
--
-- Name: idx_shadow_patterns_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_patterns_type ON public.shadow_patterns USING btree (pattern_type);
--
-- Name: idx_shadow_patterns_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_patterns_user ON public.shadow_patterns USING btree (user_id);
--
-- Name: idx_shadow_positions_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_positions_ticker ON public.shadow_positions USING btree (ticker);
--
-- Name: idx_shadow_positions_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_positions_updated ON public.shadow_positions USING btree (last_updated DESC);
--
-- Name: idx_shadow_positions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_positions_user ON public.shadow_positions USING btree (user_id);
--
-- Name: idx_shadow_snapshots_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_snapshots_date ON public.shadow_portfolio_snapshots USING btree (snapshot_date DESC);
--
-- Name: idx_shadow_snapshots_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_snapshots_user ON public.shadow_portfolio_snapshots USING btree (user_id);
--
-- Name: idx_shadow_trades_analysis_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_analysis_timestamp ON public.shadow_trades USING btree (analysis_timestamp DESC);
--
-- Name: idx_shadow_trades_market_context_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_market_context_gin ON public.shadow_trades USING gin (market_context);
--
-- Name: idx_shadow_trades_orthodox_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_orthodox_status ON public.shadow_trades USING btree (orthodox_status);
--
-- Name: idx_shadow_trades_pattern_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_pattern_type ON public.shadow_trades USING btree (pattern_type);
--
-- Name: idx_shadow_trades_signal_strength; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_signal_strength ON public.shadow_trades USING btree (signal_strength DESC);
--
-- Name: idx_shadow_trades_technical_indicators_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_technical_indicators_gin ON public.shadow_trades USING gin (technical_indicators);
--
-- Name: idx_shadow_trades_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_ticker ON public.shadow_trades USING btree (ticker);
--
-- Name: idx_shadow_trades_ticker_pattern_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_ticker_pattern_time ON public.shadow_trades USING btree (ticker, pattern_type, analysis_timestamp DESC);
--
-- Name: idx_shadow_trades_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_trades_user_id ON public.shadow_trades USING btree (user_id);
--
-- Name: idx_shadow_transactions_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_transactions_date ON public.shadow_transactions USING btree (transaction_date DESC);
--
-- Name: idx_shadow_transactions_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_transactions_order ON public.shadow_transactions USING btree (order_id);
--
-- Name: idx_shadow_transactions_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_transactions_ticker ON public.shadow_transactions USING btree (ticker);
--
-- Name: idx_shadow_transactions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shadow_transactions_user ON public.shadow_transactions USING btree (user_id);
--
-- Name: idx_snapshots_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_snapshots_created_at ON public.shadow_portfolio_snapshots USING btree (created_at DESC);
--
-- Name: idx_snapshots_demo_mode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_snapshots_demo_mode ON public.shadow_portfolio_snapshots USING btree (is_demo_mode);
--
-- Name: idx_snapshots_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_snapshots_user_created ON public.shadow_portfolio_snapshots USING btree (user_id, created_at DESC);
--
-- Name: idx_telegram_chat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_telegram_chat_id ON public.user_autopilot_settings USING btree (telegram_chat_id) WHERE (telegram_chat_id IS NOT NULL);
--
-- Name: idx_ticker_metadata_industry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ticker_metadata_industry ON public.ticker_metadata USING btree (industry);
--
-- Name: idx_ticker_metadata_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ticker_metadata_is_active ON public.ticker_metadata USING btree (is_active);
--
-- Name: idx_ticker_metadata_sector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ticker_metadata_sector ON public.ticker_metadata USING btree (sector);
--
-- Name: idx_tickers_active_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_active_type ON public.tickers USING btree (active, type);
--
-- Name: idx_tickers_aliases; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_aliases ON public.tickers USING gin (aliases);
--
-- Name: idx_tickers_fund_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_fund_category ON public.tickers USING btree (fund_category);
--
-- Name: idx_tickers_industry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_industry ON public.tickers USING btree (industry);
--
-- Name: idx_tickers_isin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_isin ON public.tickers USING btree (isin);
--
-- Name: idx_tickers_logo_url; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_logo_url ON public.tickers USING btree (ticker) WHERE (logo_url IS NOT NULL);
--
-- Name: idx_tickers_provider; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_provider ON public.tickers USING btree (provider);
--
-- Name: idx_tickers_sector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_sector ON public.tickers USING btree (sector);
--
-- Name: idx_tickers_sector_industry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_sector_industry ON public.tickers USING btree (sector, industry);
--
-- Name: idx_tickers_type_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickers_type_active ON public.tickers USING btree (type, active);
--
-- Name: idx_timeline_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timeline_created_at ON public.user_analysis_timeline USING btree (created_at DESC);
--
-- Name: idx_timeline_user_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timeline_user_date ON public.user_analysis_timeline USING btree (user_id, created_at DESC);
--
-- Name: idx_timeline_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timeline_user_id ON public.user_analysis_timeline USING btree (user_id);
--
-- Name: idx_trend_ticker_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trend_ticker_time ON public.trend_logs USING btree (ticker, "timestamp" DESC);
--
-- Name: idx_user_portfolios_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_portfolios_user_id ON public.user_portfolios USING btree (user_id);
--
-- Name: idx_user_subscriptions_keycloak; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_subscriptions_keycloak ON public.user_subscriptions USING btree (keycloak_id);
--
-- Name: idx_user_subscriptions_tier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_subscriptions_tier ON public.user_subscriptions USING btree (tier);
--
-- Name: idx_vare_adaptations_param; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vare_adaptations_param ON public.vare_adaptations USING btree (parameter, created_at DESC);
--
-- Name: idx_vare_adaptations_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vare_adaptations_time ON public.vare_adaptations USING btree (created_at DESC);
--
-- Name: idx_vare_ticker_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vare_ticker_timestamp ON public.vare_risk_scores USING btree (ticker, created_at DESC);
--
-- Name: idx_vola_ticker_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vola_ticker_time ON public.volatility_logs USING btree (ticker, "timestamp" DESC);
--
-- Name: idx_weaver_queries_concepts_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weaver_queries_concepts_gin ON public.weaver_queries USING gin (concepts);
--
-- Name: idx_weaver_queries_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weaver_queries_user_created ON public.weaver_queries USING btree (user_id, created_at);
--
-- Name: momentum_logs_ticker_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX momentum_logs_ticker_idx ON public.momentum_logs USING btree (ticker);
--
-- Name: momentum_logs_ticker_timestamp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX momentum_logs_ticker_timestamp_idx ON public.momentum_logs USING btree (ticker, "timestamp" DESC);
--
-- Name: momentum_logs_timestamp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX momentum_logs_timestamp_idx ON public.momentum_logs USING btree ("timestamp" DESC);
--
-- Name: vault_delivery_jobs_created_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vault_delivery_jobs_created_at_idx ON public.vault_delivery_jobs USING btree (created_at DESC);
--
-- Name: vault_delivery_jobs_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vault_delivery_jobs_status_idx ON public.vault_delivery_jobs USING btree (status);
--
-- Name: vault_events_created_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vault_events_created_at_idx ON public.vault_events USING btree ("timestamp" DESC);
--
-- Name: vault_events_keeper_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vault_events_keeper_idx ON public.vault_events USING btree (keeper, event_type);
--
-- Name: vault_history_created_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vault_history_created_at_idx ON public.vault_history USING btree (created_at DESC);
--
-- Name: vault_keepers_backups_created_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vault_keepers_backups_created_at_idx ON public.vault_keepers_backups USING btree (created_at DESC);
--
-- Name: vault_keepers_backups_type_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX vault_keepers_backups_type_idx ON public.vault_keepers_backups USING btree (backup_type);
--
-- Name: ledger_recent_activity _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.ledger_recent_activity AS
 SELECT la.id AS batch_id,
    la.batch_size AS event_count,
    la.merkle_root,
    la.blockchain_txid AS txid,
    la.blockchain_network AS network,
    la.anchored_at,
    la.verified,
    count(af.id) AS events_linked
   FROM (public.ledger_anchors la
     LEFT JOIN public.audit_findings af ON ((af.ledger_batch_id = la.id)))
  GROUP BY la.id
  ORDER BY la.anchored_at DESC
 LIMIT 100;
--
-- Name: audit_findings audit_findings_audit_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_findings
    ADD CONSTRAINT audit_findings_audit_session_id_fkey FOREIGN KEY (audit_session_id) REFERENCES public.audit_sessions(id);
--
-- Name: audit_findings audit_findings_ledger_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_findings
    ADD CONSTRAINT audit_findings_ledger_batch_id_fkey FOREIGN KEY (ledger_batch_id) REFERENCES public.ledger_anchors(id);
--
-- Name: autopilot_actions autopilot_actions_insight_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.autopilot_actions
    ADD CONSTRAINT autopilot_actions_insight_id_fkey FOREIGN KEY (insight_id) REFERENCES public.guardian_insights(insight_id);
--
-- Name: dependency_scans dependency_scans_audit_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dependency_scans
    ADD CONSTRAINT dependency_scans_audit_session_id_fkey FOREIGN KEY (audit_session_id) REFERENCES public.audit_sessions(id);
--
-- Name: factor_explanations factor_explanations_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.factor_explanations
    ADD CONSTRAINT factor_explanations_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.screener_results(id) ON DELETE CASCADE;
--
-- Name: factor_scores factor_scores_ticker_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.factor_scores
    ADD CONSTRAINT factor_scores_ticker_fkey FOREIGN KEY (ticker) REFERENCES public.tickers(ticker);
--
-- Name: guardian_insights fk_guardian_snapshot; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guardian_insights
    ADD CONSTRAINT fk_guardian_snapshot FOREIGN KEY (snapshot_id) REFERENCES public.shadow_portfolio_snapshots(snapshot_id) ON DELETE CASCADE;
--
-- Name: shadow_orders fk_shadow_orders_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_orders
    ADD CONSTRAINT fk_shadow_orders_user FOREIGN KEY (user_id) REFERENCES public.shadow_cash_accounts(user_id) ON DELETE CASCADE;
--
-- Name: shadow_positions fk_shadow_positions_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_positions
    ADD CONSTRAINT fk_shadow_positions_user FOREIGN KEY (user_id) REFERENCES public.shadow_cash_accounts(user_id) ON DELETE CASCADE;
--
-- Name: shadow_portfolio_snapshots fk_shadow_snapshots_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_portfolio_snapshots
    ADD CONSTRAINT fk_shadow_snapshots_user FOREIGN KEY (user_id) REFERENCES public.shadow_cash_accounts(user_id) ON DELETE CASCADE;
--
-- Name: shadow_transactions fk_shadow_transactions_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shadow_transactions
    ADD CONSTRAINT fk_shadow_transactions_order FOREIGN KEY (order_id) REFERENCES public.shadow_orders(order_id) ON DELETE SET NULL;
--
-- Name: screener_features screener_features_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screener_features
    ADD CONSTRAINT screener_features_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.screener_results(id) ON DELETE CASCADE;
--
-- Name: user_autopilot_settings user_autopilot_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_autopilot_settings
    ADD CONSTRAINT user_autopilot_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.shadow_cash_accounts(user_id) ON DELETE CASCADE;

-- =============================================================================
-- Mercator-Specific Extensions
-- =============================================================================

-- MCP Tool Calls tracking (from mercator init-scripts/003_create_mcp_tables.sql)
-- Already in schema as mcp_tool_calls if inherited from vitruvyan.
-- This ensures it exists even if vitruvyan didn't have it:
CREATE TABLE IF NOT EXISTS public.mcp_tool_calls (
    conclave_id UUID PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL,
    args JSONB NOT NULL,
    result JSONB NOT NULL,
    orthodoxy_status VARCHAR(20) NOT NULL CHECK (orthodoxy_status IN ('blessed', 'purified', 'heretical')),
    user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    execution_time_ms FLOAT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_user ON public.mcp_tool_calls(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_tool ON public.mcp_tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_created ON public.mcp_tool_calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_orthodoxy ON public.mcp_tool_calls(orthodoxy_status);

-- =============================================================================
-- End of Mercator Schema
-- =============================================================================
