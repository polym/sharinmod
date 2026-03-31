--
-- PostgreSQL database dump
--

\restrict MKynrWIp6U1hGOcY1c5WEnoNVZEwtBxEu80hJaanaKuZBjCwgImcK6XjuzSTxwx

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: provider_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provider_models (
    id integer NOT NULL,
    provider_config_id integer NOT NULL,
    model_key character varying NOT NULL,
    display_name character varying NOT NULL,
    description character varying,
    context_length character varying NOT NULL,
    max_output_length character varying NOT NULL,
    input_types json,
    output_types json,
    coding_score integer,
    is_enabled boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    real_model character varying(200)
);


--
-- Name: provider_models_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.provider_models_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: provider_models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.provider_models_id_seq OWNED BY public.provider_models.id;


--
-- Name: provider_models id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_models ALTER COLUMN id SET DEFAULT nextval('public.provider_models_id_seq'::regclass);


--
-- Data for Name: provider_models; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.provider_models (id, provider_config_id, model_key, display_name, description, context_length, max_output_length, input_types, output_types, coding_score, is_enabled, created_at, updated_at, real_model) FROM stdin;
1	1	glm-4.5-air	GLM-4.5 Air	智谱 AI 轻量级模型，快速响应适合简单任务	128k	4k	["Text"]	["Text"]	\N	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
2	1	glm-4.6	GLM-4.6	智谱 AI 高性能模型，平衡速度与质量	128k	4k	["Text"]	["Text"]	1356	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
5	2	glm-4.5-air	GLM-4.5 Air	智谱 AI 轻量级模型，快速响应适合简单任务	128k	4k	["Text"]	["Text"]	\N	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
6	2	glm-4.6	GLM-4.6	智谱 AI 高性能模型，平衡速度与质量	128k	4k	["Text"]	["Text"]	1356	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
11	3	kimi-k2	Kimi K2	Kimi K2 模型	128k	128k	["Text", "Image", "Video"]	["Text"]	1330	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
12	3	kimi-k2.5	Kimi K2.5	Kimi K2.5 高性能模型	128k	128k	["Text", "Image", "Video"]	["Text"]	1447	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
13	3	doubao-seed-code	Doubao Seed Code	豆包种子代码模型，专注于代码生成和理解	256k	32k	["Text", "Image"]	["Text"]	1014	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
14	4	kimi-k2.5	Kimi K2.5	Kimi K2.5 高性能模型	128k	128k	["Text", "Image", "Video"]	["Text"]	1447	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
15	5	minimax-m2.1	MiniMax M2.1	MiniMax M2.1 高性能代码模型，230B 总参数，10B 激活参数	196k	65k	["Text"]	["Text"]	1409	t	2026-02-13 03:31:28.864248	2026-02-13 03:31:28.864248	\N
18	5	minimax-m2.5	MiniMax M2.5	\N	128k	4k	["text"]	["text"]	\N	t	2026-02-14 01:43:56.163085	2026-02-14 01:43:56.163087	\N
28	10	glm-5	GLM-5	智谱 AI 最新一代旗舰模型，超长上下文支持	200k	4k	["Text"]	["Text"]	1451	t	2026-03-05 15:19:48.857828	2026-03-05 15:19:48.85783	\N
9	3	deepseek-v3.2	DeepSeek V3.2	DeepSeek V3.2 高性能模型	128k	8k	["Text"]	["Text"]	1377	t	2026-02-13 03:31:28.864248	2026-02-27 03:37:35.309223	\N
4	1	glm-5	GLM-5	智谱 AI 最新一代旗舰模型，超长上下文支持	200k	4k	["Text"]	["Text"]	\N	f	2026-02-13 03:31:28.864248	2026-02-27 04:09:36.552596	\N
30	9	minimax-m2.5	MiniMax M2.5	由稀宇科技（MiniMax）于 2026 年 2 月推出的新一代旗舰级大语言模型。它被定位为**“原生 Agent（智能体）生产级模型”**，特别针对复杂任务的拆解、代码编写以及自动化办公场景进行了深度优化。	200k	4k	["Text"]	["Text"]	1422	t	2026-03-06 10:46:47.010182	2026-03-06 14:29:46.378314	\N
20	8	glm-5	GLM-5	\N	200k	4k	["Text", "Image"]	["Text"]	\N	t	2026-02-26 15:30:24.395963	2026-02-27 04:10:40.093179	\N
10	3	glm-4.7	GLM 4.7	智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力	128k	4k	["Text"]	["Text"]	1441	t	2026-02-13 03:31:28.864248	2026-02-28 14:49:34.404669	\N
7	2	glm-4.7	GLM 4.7	智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力	128k	4k	["Text"]	["Text"]	1441	t	2026-02-13 03:31:28.864248	2026-02-28 14:49:34.405968	\N
3	1	glm-4.7	GLM 4.7	智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力	128k	4k	["Text"]	["Text"]	1441	t	2026-02-13 03:31:28.864248	2026-02-28 14:49:34.406224	\N
8	2	glm-5	GLM-5	智谱 AI 最新一代旗舰模型，超长上下文支持	200k	4k	["Text"]	["Text"]	1456	f	2026-02-13 03:31:28.864248	2026-02-28 23:09:04.181424	\N
21	8	kimi-k2.5	Kimi K2.5	Kimi K2.5 高性能模型	128k	128k	["Text", "Image", "Video"]	["Text"]	1447	t	2026-03-04 06:14:27.626052	2026-03-04 06:14:27.626053	\N
22	8	glm-4.7	GLM-4.7	\N	128k	4k	["Text"]	["Text"]	\N	t	2026-03-04 06:15:44.528992	2026-03-04 06:15:44.528994	\N
23	8	qwen3.5-plus	Qwen3.5-Plus	阿里巴巴通义千问团队在 2026 年 2 月 16 日 正式发布的新一代大语言模型。它是 Qwen3.5 系列中的高性能版本，旨在平衡极致的推理效率与顶尖的智能水平。	1024k	4k	["Text", "Image"]	["Text"]	\N	t	2026-03-04 06:21:07.854329	2026-03-04 06:21:07.854331	\N
24	9	glm-5	GLM-5	智谱 AI 最新一代旗舰模型，超长上下文支持	200k	4k	["Text"]	["Text"]	1451	t	2026-03-04 06:38:20.504921	2026-03-04 06:38:20.504922	\N
25	9	kimi-k2.5	Kimi K2.5	Kimi K2.5 高性能模型	128k	128k	["Text", "Image", "Video"]	["Text"]	1447	t	2026-03-04 06:38:28.613007	2026-03-04 06:38:28.613009	\N
26	10	claude-sonnet-4-6	Claude Sonnet 4.6	Claude 4 系列中的中坚力量，其性能在多个维度上甚至超越了早期的 Opus 级模型（如 Opus 4.5），被誉为“性价比与智能的巅峰结合”。	1024k	128K	["Text", "Image"]	["Text"]	1524	t	2026-03-04 09:42:49.660495	2026-03-04 09:42:49.660497	\N
27	10	claude-opus-4-6	Claude Opus 4.6	Anthropic 于 2026 年 2 月 5 日 发布的最强旗舰模型，也是 Claude 4 家族中的“智力天花板”。它在复杂推理、长文档处理和自主 Agent 协作方面树立了新的行业标杆。	1024k	128k	["Text", "Image"]	["Text"]	1557	t	2026-03-04 09:48:11.699514	2026-03-04 09:48:11.699517	\N
29	8	minimax-m2.5	MiniMax M2.5	由稀宇科技（MiniMax）于 2026 年 2 月推出的新一代旗舰级大语言模型。它被定位为**“原生 Agent（智能体）生产级模型”**，特别针对复杂任务的拆解、代码编写以及自动化办公场景进行了深度优化。	200k	4k	["Text"]	["Text"]	1422	t	2026-03-06 10:46:16.753774	2026-03-06 14:56:41.447726	MiniMax-M2.5
31	10	glm-4.7	GLM-4.7	\N	128k	16k	["Text"]	["Text"]	\N	t	2026-03-07 15:34:19.793925	2026-03-07 15:34:19.793927	\N
32	3	doubao-seed-2.0-pro	Doubao-Seed-2.0-pro	字节跳动在 2026 年 2 月 14 日正式发布的旗舰级全能通用大模型。它是豆包大模型进入“2.0 时代”的核心产品，旨在面向 Agent（智能体） 时代，解决真实世界中的复杂推理与长链路任务。	1024k	8k	["Text", "Image"]	["Text"]	\N	t	2026-03-11 09:25:06.719407	2026-03-11 09:25:06.719409	\N
33	3	doubao-seed-2.0-lite	Doubao-Seed-2.0-lite	节跳动在 2026 年 2 月推出的 “效能标杆” 模型。它作为 Seed-2.0 系列的中坚力量，核心目标是在保持接近旗舰级性能的同时，大幅提升响应速度并降低成本。	256k	128k	["Text", "Image", "Video"]	["Text"]	\N	t	2026-03-11 09:32:45.465363	2026-03-11 09:32:45.465367	\N
\.


--
-- Name: provider_models_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.provider_models_id_seq', 33, true);


--
-- Name: provider_models provider_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_models
    ADD CONSTRAINT provider_models_pkey PRIMARY KEY (id);


--
-- Name: idx_provider_model_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_provider_model_unique ON public.provider_models USING btree (provider_config_id, model_key);


--
-- Name: ix_provider_models_is_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_provider_models_is_enabled ON public.provider_models USING btree (is_enabled);


--
-- Name: ix_provider_models_provider_config_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_provider_models_provider_config_id ON public.provider_models USING btree (provider_config_id);


--
-- Name: provider_models provider_models_provider_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_models
    ADD CONSTRAINT provider_models_provider_config_id_fkey FOREIGN KEY (provider_config_id) REFERENCES public.provider_configs(id);


--
-- PostgreSQL database dump complete
--

\unrestrict MKynrWIp6U1hGOcY1c5WEnoNVZEwtBxEu80hJaanaKuZBjCwgImcK6XjuzSTxwx

