--
-- PostgreSQL database dump
--

\restrict h9ZPbolvCueoa1iwds2aqbXojlgmr4NJ2jbw26QdABu0fAcb47crxJVskShZVQE

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id bigint NOT NULL,
    user_id bigint,
    action character varying(100) NOT NULL,
    entity_name character varying(100) NOT NULL,
    entity_id bigint,
    ip_address character varying(45),
    user_agent text,
    details jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: bom_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bom_items (
    id bigint NOT NULL,
    bom_template_id bigint NOT NULL,
    product_id bigint NOT NULL,
    item_category character varying(100) NOT NULL,
    default_quantity numeric(10,2) NOT NULL,
    unit_of_measure character varying(50) NOT NULL,
    is_mandatory boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_bom_item_default_qty CHECK ((default_quantity > (0)::numeric))
);


--
-- Name: bom_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bom_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bom_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bom_items_id_seq OWNED BY public.bom_items.id;


--
-- Name: bom_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bom_templates (
    id bigint NOT NULL,
    template_name character varying(150) NOT NULL,
    system_type character varying(50) NOT NULL,
    capacity_kw numeric(5,2) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_bom_template_capacity CHECK ((capacity_kw > (0)::numeric))
);


--
-- Name: bom_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bom_templates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bom_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bom_templates_id_seq OWNED BY public.bom_templates.id;


--
-- Name: customer_acceptances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_acceptances (
    id bigint NOT NULL,
    installation_id bigint NOT NULL,
    project_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    acceptance_date date NOT NULL,
    rating_overall bigint,
    satisfaction_notes text,
    customer_signature_id bigint,
    is_accepted boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_customer_rating_range CHECK (((rating_overall IS NULL) OR ((rating_overall >= 1) AND (rating_overall <= 5))))
);


--
-- Name: customer_acceptances_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customer_acceptances_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customer_acceptances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customer_acceptances_id_seq OWNED BY public.customer_acceptances.id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    id bigint NOT NULL,
    user_id bigint,
    customer_type character varying(50) NOT NULL,
    full_name character varying(255) NOT NULL,
    email character varying(255),
    phone character varying(30) NOT NULL,
    alternate_phone character varying(30),
    address text NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    pincode character varying(20) NOT NULL,
    electricity_consumer_number character varying(100),
    sanctioned_load_kw numeric(6,2),
    created_by bigint NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_customer_sanctioned_load CHECK (((sanctioned_load_kw IS NULL) OR (sanctioned_load_kw >= (0)::numeric)))
);


--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;


--
-- Name: delivery_confirmations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.delivery_confirmations (
    id bigint NOT NULL,
    dispatch_id bigint NOT NULL,
    project_id bigint NOT NULL,
    confirmed_by bigint NOT NULL,
    confirmation_type character varying(50) NOT NULL,
    recipient_name character varying(150) NOT NULL,
    recipient_phone character varying(30) NOT NULL,
    confirmation_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    signature_attachment_id bigint,
    delivery_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: delivery_confirmations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.delivery_confirmations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: delivery_confirmations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.delivery_confirmations_id_seq OWNED BY public.delivery_confirmations.id;


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id bigint NOT NULL,
    name character varying(150) NOT NULL,
    code character varying(50) NOT NULL,
    manager_id bigint,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: departments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.departments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
-- Name: dispatch_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dispatch_items (
    id bigint NOT NULL,
    dispatch_id bigint NOT NULL,
    product_id bigint NOT NULL,
    dispatched_quantity numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_dispatch_item_qty_positive CHECK ((dispatched_quantity > (0)::numeric))
);


--
-- Name: dispatch_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dispatch_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dispatch_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dispatch_items_id_seq OWNED BY public.dispatch_items.id;


--
-- Name: dispatch_serials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dispatch_serials (
    id bigint NOT NULL,
    dispatch_item_id bigint NOT NULL,
    serial_number_id bigint NOT NULL,
    scanned_at timestamp with time zone DEFAULT now() NOT NULL,
    scanned_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dispatch_serials_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dispatch_serials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dispatch_serials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dispatch_serials_id_seq OWNED BY public.dispatch_serials.id;


--
-- Name: dispatches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dispatches (
    id bigint NOT NULL,
    dispatch_number character varying(50) NOT NULL,
    project_id bigint NOT NULL,
    order_id bigint NOT NULL,
    dispatched_date date NOT NULL,
    dispatch_status character varying(50) NOT NULL,
    vehicle_number character varying(50),
    driver_name character varying(150),
    driver_phone character varying(30),
    tracking_number character varying(100),
    dispatched_by bigint NOT NULL,
    remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dispatches_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dispatches_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dispatches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dispatches_id_seq OWNED BY public.dispatches.id;


--
-- Name: employee_certifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_certifications (
    id bigint NOT NULL,
    employee_id bigint NOT NULL,
    certification_name character varying(255) NOT NULL,
    issuing_authority character varying(255) NOT NULL,
    certificate_number character varying(100),
    issue_date date NOT NULL,
    expiry_date date,
    attachment_id bigint,
    verification_status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_certification_dates CHECK (((expiry_date IS NULL) OR (expiry_date >= issue_date)))
);


--
-- Name: employee_certifications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_certifications_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_certifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_certifications_id_seq OWNED BY public.employee_certifications.id;


--
-- Name: employee_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_skills (
    id bigint NOT NULL,
    employee_id bigint NOT NULL,
    skill_id bigint NOT NULL,
    proficiency_level character varying(50) NOT NULL,
    years_of_experience numeric(4,1) NOT NULL,
    verified_by bigint,
    verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_skill_experience_non_negative CHECK ((years_of_experience >= (0)::numeric))
);


--
-- Name: employee_skills_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_skills_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_skills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_skills_id_seq OWNED BY public.employee_skills.id;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    department_id bigint NOT NULL,
    employee_code character varying(50) NOT NULL,
    designation character varying(100) NOT NULL,
    employment_type character varying(50) NOT NULL,
    joining_date date NOT NULL,
    exit_date date,
    emergency_contact character varying(100),
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_employee_exit_date CHECK (((exit_date IS NULL) OR (exit_date >= joining_date)))
);


--
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employees_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- Name: enquiries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enquiries (
    id bigint NOT NULL,
    customer_id bigint NOT NULL,
    enquiry_number character varying(50) NOT NULL,
    source character varying(50) NOT NULL,
    system_type character varying(50) NOT NULL,
    proposed_capacity_kw numeric(5,2) NOT NULL,
    monthly_electricity_bill numeric(12,2),
    roof_type character varying(100),
    status character varying(50) NOT NULL,
    assigned_sales_id bigint,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_enquiry_bill_non_negative CHECK (((monthly_electricity_bill IS NULL) OR (monthly_electricity_bill >= (0)::numeric))),
    CONSTRAINT chk_enquiry_capacity_positive CHECK ((proposed_capacity_kw > (0)::numeric))
);


--
-- Name: enquiries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.enquiries_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: enquiries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.enquiries_id_seq OWNED BY public.enquiries.id;


--
-- Name: escalations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.escalations (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    project_id bigint,
    escalated_by bigint NOT NULL,
    escalated_to bigint NOT NULL,
    escalation_level character varying(50) NOT NULL,
    reason text NOT NULL,
    resolution_notes text,
    is_resolved boolean NOT NULL,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: escalations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.escalations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: escalations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.escalations_id_seq OWNED BY public.escalations.id;


--
-- Name: expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expenses (
    id bigint NOT NULL,
    expense_number character varying(50) NOT NULL,
    project_id bigint,
    department_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    expense_category character varying(50) NOT NULL,
    expense_date date NOT NULL,
    amount numeric(12,2) NOT NULL,
    tax_amount numeric(12,2) NOT NULL,
    payment_status character varying(50) NOT NULL,
    approved_by bigint,
    receipt_attachment_id bigint,
    description text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_expense_amount_positive CHECK ((amount > (0)::numeric)),
    CONSTRAINT chk_expense_tax_non_negative CHECK ((tax_amount >= (0)::numeric))
);


--
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expenses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- Name: file_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.file_attachments (
    id bigint NOT NULL,
    entity_type character varying(100) NOT NULL,
    entity_id bigint NOT NULL,
    file_name character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size_bytes bigint NOT NULL,
    mime_type character varying(100) NOT NULL,
    storage_backend character varying(50) NOT NULL,
    checksum_sha256 character varying(64),
    uploaded_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_file_size_non_negative CHECK ((file_size_bytes >= 0))
);


--
-- Name: file_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.file_attachments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: file_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.file_attachments_id_seq OWNED BY public.file_attachments.id;


--
-- Name: followups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.followups (
    id bigint NOT NULL,
    enquiry_id bigint NOT NULL,
    conducted_by bigint NOT NULL,
    followup_type character varying(50) NOT NULL,
    scheduled_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    status character varying(50) NOT NULL,
    discussion_summary text,
    next_followup_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: followups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.followups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: followups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.followups_id_seq OWNED BY public.followups.id;


--
-- Name: goods_receipt_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.goods_receipt_items (
    id bigint NOT NULL,
    goods_receipt_id bigint NOT NULL,
    po_item_id bigint NOT NULL,
    product_id bigint NOT NULL,
    received_quantity numeric(10,2) NOT NULL,
    accepted_quantity numeric(10,2) NOT NULL,
    rejected_quantity numeric(10,2) NOT NULL,
    rejection_reason character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_grn_item_accepted_qty CHECK ((accepted_quantity >= (0)::numeric)),
    CONSTRAINT chk_grn_item_balance CHECK ((received_quantity = (accepted_quantity + rejected_quantity))),
    CONSTRAINT chk_grn_item_received_qty CHECK ((received_quantity >= (0)::numeric)),
    CONSTRAINT chk_grn_item_rejected_qty CHECK ((rejected_quantity >= (0)::numeric))
);


--
-- Name: goods_receipt_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.goods_receipt_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: goods_receipt_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.goods_receipt_items_id_seq OWNED BY public.goods_receipt_items.id;


--
-- Name: goods_receipts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.goods_receipts (
    id bigint NOT NULL,
    grn_number character varying(50) NOT NULL,
    purchase_order_id bigint NOT NULL,
    supplier_id bigint NOT NULL,
    received_date date NOT NULL,
    received_by bigint NOT NULL,
    challan_number character varying(100),
    challan_date date,
    status character varying(50) NOT NULL,
    inspection_remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: goods_receipts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.goods_receipts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: goods_receipts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.goods_receipts_id_seq OWNED BY public.goods_receipts.id;


--
-- Name: installation_checklists; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installation_checklists (
    id bigint NOT NULL,
    installation_id bigint NOT NULL,
    checklist_item character varying(255) NOT NULL,
    category character varying(50) NOT NULL,
    is_checked boolean NOT NULL,
    remarks text,
    verified_by bigint,
    verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: installation_checklists_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installation_checklists_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installation_checklists_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installation_checklists_id_seq OWNED BY public.installation_checklists.id;


--
-- Name: installation_photos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installation_photos (
    id bigint NOT NULL,
    installation_id bigint NOT NULL,
    stage character varying(50) NOT NULL,
    attachment_id bigint NOT NULL,
    caption character varying(255),
    gps_latitude numeric(10,7),
    gps_longitude numeric(10,7),
    captured_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: installation_photos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installation_photos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installation_photos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installation_photos_id_seq OWNED BY public.installation_photos.id;


--
-- Name: installation_schedule_technicians; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installation_schedule_technicians (
    id bigint NOT NULL,
    schedule_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    role_in_team character varying(50) NOT NULL,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: installation_schedule_technicians_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installation_schedule_technicians_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installation_schedule_technicians_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installation_schedule_technicians_id_seq OWNED BY public.installation_schedule_technicians.id;


--
-- Name: installation_schedules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installation_schedules (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    scheduled_start_date date NOT NULL,
    scheduled_end_date date NOT NULL,
    actual_start_date date,
    actual_end_date date,
    status character varying(50) NOT NULL,
    notes text,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_schedule_actual_dates CHECK (((actual_end_date IS NULL) OR (actual_start_date IS NULL) OR (actual_end_date >= actual_start_date))),
    CONSTRAINT chk_schedule_planned_dates CHECK ((scheduled_end_date >= scheduled_start_date))
);


--
-- Name: installation_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installation_schedules_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installation_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installation_schedules_id_seq OWNED BY public.installation_schedules.id;


--
-- Name: installation_tests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installation_tests (
    id bigint NOT NULL,
    installation_id bigint NOT NULL,
    test_name character varying(100) NOT NULL,
    standard_value character varying(100),
    measured_value character varying(100) NOT NULL,
    unit_of_measure character varying(30) NOT NULL,
    is_passed boolean NOT NULL,
    tested_by bigint NOT NULL,
    test_date date NOT NULL,
    remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: installation_tests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installation_tests_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installation_tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installation_tests_id_seq OWNED BY public.installation_tests.id;


--
-- Name: installations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.installations (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    schedule_id bigint,
    lead_technician_id bigint NOT NULL,
    system_capacity_kw numeric(5,2) NOT NULL,
    inverter_make_model character varying(150),
    total_panels_installed bigint NOT NULL,
    structure_type character varying(100),
    installation_date date NOT NULL,
    commissioning_date date,
    status character varying(50) NOT NULL,
    technician_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_installation_capacity CHECK ((system_capacity_kw > (0)::numeric)),
    CONSTRAINT chk_installation_dates CHECK (((commissioning_date IS NULL) OR (commissioning_date >= installation_date))),
    CONSTRAINT chk_installation_panels_installed CHECK ((total_panels_installed >= 0))
);


--
-- Name: installations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.installations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: installations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.installations_id_seq OWNED BY public.installations.id;


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    warehouse_location character varying(100) NOT NULL,
    quantity_on_hand numeric(12,2) NOT NULL,
    reserved_quantity numeric(12,2) NOT NULL,
    quantity_available numeric(12,2) NOT NULL,
    average_unit_cost numeric(12,2) NOT NULL,
    reorder_level numeric(10,2) NOT NULL,
    last_restocked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_inventory_available_non_negative CHECK ((quantity_available >= (0)::numeric)),
    CONSTRAINT chk_inventory_qoh_ge_reserved CHECK ((quantity_on_hand >= reserved_quantity)),
    CONSTRAINT chk_inventory_qoh_non_negative CHECK ((quantity_on_hand >= (0)::numeric)),
    CONSTRAINT chk_inventory_reorder_non_negative CHECK ((reorder_level >= (0)::numeric)),
    CONSTRAINT chk_inventory_reserved_non_negative CHECK ((reserved_quantity >= (0)::numeric))
);


--
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- Name: invoice_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invoice_items (
    id bigint NOT NULL,
    invoice_id bigint NOT NULL,
    product_id bigint NOT NULL,
    item_description character varying(255) NOT NULL,
    quantity numeric(10,2) NOT NULL,
    unit_price numeric(12,2) NOT NULL,
    tax_rate_percent numeric(5,2) NOT NULL,
    total_amount numeric(12,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_invoice_item_price_non_negative CHECK ((unit_price >= (0)::numeric)),
    CONSTRAINT chk_invoice_item_qty_positive CHECK ((quantity > (0)::numeric)),
    CONSTRAINT chk_invoice_item_total_non_negative CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: invoice_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.invoice_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: invoice_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.invoice_items_id_seq OWNED BY public.invoice_items.id;


--
-- Name: invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invoices (
    id bigint NOT NULL,
    invoice_number character varying(50) NOT NULL,
    order_id bigint NOT NULL,
    project_id bigint,
    customer_id bigint NOT NULL,
    invoice_type character varying(50) NOT NULL,
    invoice_date date NOT NULL,
    due_date date NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    tax_amount numeric(12,2) NOT NULL,
    total_amount numeric(12,2) NOT NULL,
    paid_amount numeric(12,2) NOT NULL,
    balance_amount numeric(12,2) NOT NULL,
    payment_status character varying(50) NOT NULL,
    pdf_attachment_id bigint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_invoice_balance_non_negative CHECK ((balance_amount >= (0)::numeric)),
    CONSTRAINT chk_invoice_dates CHECK ((due_date >= invoice_date)),
    CONSTRAINT chk_invoice_paid_non_negative CHECK ((paid_amount >= (0)::numeric)),
    CONSTRAINT chk_invoice_total_non_negative CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: invoices_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.invoices_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: invoices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.invoices_id_seq OWNED BY public.invoices.id;


--
-- Name: material_consumption; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.material_consumption (
    id bigint NOT NULL,
    installation_id bigint NOT NULL,
    product_id bigint NOT NULL,
    serial_number_id bigint,
    quantity_consumed numeric(10,2) NOT NULL,
    unit_of_measure character varying(50) NOT NULL,
    is_extra_material boolean NOT NULL,
    remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_mat_consumption_qty_positive CHECK ((quantity_consumed > (0)::numeric))
);


--
-- Name: material_consumption_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.material_consumption_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: material_consumption_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.material_consumption_id_seq OWNED BY public.material_consumption.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    notification_type character varying(50) NOT NULL,
    is_read boolean NOT NULL,
    read_at timestamp with time zone,
    link_url character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notifications_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    id bigint NOT NULL,
    order_number character varying(50) NOT NULL,
    quotation_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    order_date date NOT NULL,
    total_amount numeric(12,2) NOT NULL,
    advance_paid numeric(12,2) NOT NULL,
    balance_amount numeric(12,2) NOT NULL,
    status character varying(50) NOT NULL,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_order_advance_paid CHECK ((advance_paid >= (0)::numeric)),
    CONSTRAINT chk_order_balance_amount CHECK ((balance_amount >= (0)::numeric)),
    CONSTRAINT chk_order_total_amount CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.orders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: payment_allocations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_allocations (
    id bigint NOT NULL,
    payment_id bigint NOT NULL,
    invoice_id bigint NOT NULL,
    allocated_amount numeric(12,2) NOT NULL,
    allocated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_payment_alloc_positive CHECK ((allocated_amount > (0)::numeric))
);


--
-- Name: payment_allocations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payment_allocations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payment_allocations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payment_allocations_id_seq OWNED BY public.payment_allocations.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id bigint NOT NULL,
    payment_number character varying(50) NOT NULL,
    customer_id bigint NOT NULL,
    order_id bigint NOT NULL,
    project_id bigint,
    payment_date date NOT NULL,
    payment_method character varying(50) NOT NULL,
    transaction_reference character varying(100),
    amount numeric(12,2) NOT NULL,
    unallocated_amount numeric(12,2) NOT NULL,
    status character varying(50) NOT NULL,
    notes text,
    received_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_payment_amount_positive CHECK ((amount > (0)::numeric)),
    CONSTRAINT chk_payment_unalloc_le_amount CHECK ((unallocated_amount <= amount)),
    CONSTRAINT chk_payment_unalloc_non_negative CHECK ((unallocated_amount >= (0)::numeric))
);


--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permissions (
    id bigint NOT NULL,
    name character varying(150) NOT NULL,
    code character varying(100) NOT NULL,
    module character varying(100) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    id bigint NOT NULL,
    product_code character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    category character varying(100) NOT NULL,
    brand character varying(100),
    model_number character varying(150),
    wattage_or_capacity character varying(100),
    unit_of_measure character varying(50) NOT NULL,
    is_serialized boolean NOT NULL,
    base_price numeric(12,2) NOT NULL,
    tax_rate_percent numeric(5,2) NOT NULL,
    min_stock_alert numeric(10,2) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_product_base_price CHECK ((base_price >= (0)::numeric)),
    CONSTRAINT chk_product_min_stock CHECK ((min_stock_alert >= (0)::numeric)),
    CONSTRAINT chk_product_tax_rate CHECK ((tax_rate_percent >= (0)::numeric))
);


--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.products_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: project_bom_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_bom_items (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    product_id bigint NOT NULL,
    item_category character varying(100) NOT NULL,
    planned_quantity numeric(10,2) NOT NULL,
    allocated_quantity numeric(10,2) NOT NULL,
    dispatched_quantity numeric(10,2) NOT NULL,
    installed_quantity numeric(10,2) NOT NULL,
    unit_cost_snapshot numeric(12,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_project_bom_allocated_qty CHECK ((allocated_quantity >= (0)::numeric)),
    CONSTRAINT chk_project_bom_dispatched_qty CHECK ((dispatched_quantity >= (0)::numeric)),
    CONSTRAINT chk_project_bom_installed_qty CHECK ((installed_quantity >= (0)::numeric)),
    CONSTRAINT chk_project_bom_planned_qty CHECK ((planned_quantity >= (0)::numeric)),
    CONSTRAINT chk_project_bom_unit_cost CHECK ((unit_cost_snapshot >= (0)::numeric))
);


--
-- Name: project_bom_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_bom_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_bom_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_bom_items_id_seq OWNED BY public.project_bom_items.id;


--
-- Name: project_costs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_costs (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    cost_category character varying(50) NOT NULL,
    cost_amount numeric(12,2) NOT NULL,
    source_reference_type character varying(50) NOT NULL,
    source_reference_id bigint,
    recorded_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_project_cost_non_negative CHECK ((cost_amount >= (0)::numeric))
);


--
-- Name: project_costs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_costs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_costs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_costs_id_seq OWNED BY public.project_costs.id;


--
-- Name: project_notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_notes (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    author_id bigint NOT NULL,
    note_type character varying(50) NOT NULL,
    note_text text NOT NULL,
    is_internal boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: project_notes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_notes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_notes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_notes_id_seq OWNED BY public.project_notes.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id bigint NOT NULL,
    project_code character varying(50) NOT NULL,
    order_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    project_manager_id bigint,
    system_capacity_kw numeric(5,2) NOT NULL,
    system_type character varying(50) NOT NULL,
    site_address text NOT NULL,
    planned_start_date date NOT NULL,
    planned_completion_date date NOT NULL,
    actual_completion_date date,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_project_actual_dates CHECK (((actual_completion_date IS NULL) OR (actual_completion_date >= planned_start_date))),
    CONSTRAINT chk_project_capacity CHECK ((system_capacity_kw > (0)::numeric)),
    CONSTRAINT chk_project_planned_dates CHECK ((planned_completion_date >= planned_start_date))
);


--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.projects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: purchase_order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.purchase_order_items (
    id bigint NOT NULL,
    purchase_order_id bigint NOT NULL,
    product_id bigint NOT NULL,
    ordered_quantity numeric(10,2) NOT NULL,
    received_quantity numeric(10,2) NOT NULL,
    unit_price numeric(12,2) NOT NULL,
    tax_rate_percent numeric(5,2) NOT NULL,
    total_amount numeric(12,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_po_item_ordered_qty CHECK ((ordered_quantity > (0)::numeric)),
    CONSTRAINT chk_po_item_received_qty CHECK ((received_quantity >= (0)::numeric)),
    CONSTRAINT chk_po_item_total_amount CHECK ((total_amount >= (0)::numeric)),
    CONSTRAINT chk_po_item_unit_price CHECK ((unit_price >= (0)::numeric))
);


--
-- Name: purchase_order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.purchase_order_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: purchase_order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_order_items_id_seq OWNED BY public.purchase_order_items.id;


--
-- Name: purchase_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.purchase_orders (
    id bigint NOT NULL,
    po_number character varying(50) NOT NULL,
    supplier_id bigint NOT NULL,
    project_id bigint,
    po_date date NOT NULL,
    expected_delivery_date date,
    total_amount numeric(12,2) NOT NULL,
    tax_amount numeric(12,2) NOT NULL,
    status character varying(50) NOT NULL,
    created_by bigint NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_po_dates CHECK (((expected_delivery_date IS NULL) OR (expected_delivery_date >= po_date))),
    CONSTRAINT chk_po_tax_amount CHECK ((tax_amount >= (0)::numeric)),
    CONSTRAINT chk_po_total_amount CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: purchase_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.purchase_orders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: purchase_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_orders_id_seq OWNED BY public.purchase_orders.id;


--
-- Name: quotation_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quotation_items (
    id bigint NOT NULL,
    quotation_id bigint NOT NULL,
    product_id bigint NOT NULL,
    item_description character varying(255) NOT NULL,
    quantity numeric(10,2) NOT NULL,
    unit_price numeric(12,2) NOT NULL,
    discount_amount numeric(12,2) NOT NULL,
    tax_rate_percent numeric(5,2) NOT NULL,
    total_amount numeric(12,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_quotation_item_price CHECK ((unit_price >= (0)::numeric)),
    CONSTRAINT chk_quotation_item_qty CHECK ((quantity > (0)::numeric)),
    CONSTRAINT chk_quotation_item_total CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: quotation_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quotation_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quotation_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotation_items_id_seq OWNED BY public.quotation_items.id;


--
-- Name: quotation_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quotation_revisions (
    id bigint NOT NULL,
    quotation_id bigint NOT NULL,
    revision_number bigint NOT NULL,
    snapshot_data jsonb NOT NULL,
    reason_for_revision text NOT NULL,
    revised_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: quotation_revisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quotation_revisions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quotation_revisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotation_revisions_id_seq OWNED BY public.quotation_revisions.id;


--
-- Name: quotations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quotations (
    id bigint NOT NULL,
    enquiry_id bigint NOT NULL,
    survey_id bigint,
    quotation_number character varying(50) NOT NULL,
    version bigint NOT NULL,
    system_type character varying(50) NOT NULL,
    capacity_kw numeric(5,2) NOT NULL,
    total_product_cost numeric(12,2) NOT NULL,
    installation_cost numeric(12,2) NOT NULL,
    tax_amount numeric(12,2) NOT NULL,
    gross_amount numeric(12,2) NOT NULL,
    subsidy_estimate numeric(12,2) NOT NULL,
    net_payable_amount numeric(12,2) NOT NULL,
    status character varying(50) NOT NULL,
    valid_until date NOT NULL,
    quotation_date date NOT NULL,
    created_by bigint NOT NULL,
    terms_and_conditions text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_quotation_capacity CHECK ((capacity_kw > (0)::numeric)),
    CONSTRAINT chk_quotation_dates CHECK ((valid_until >= quotation_date)),
    CONSTRAINT chk_quotation_gross_amount CHECK ((gross_amount >= (0)::numeric)),
    CONSTRAINT chk_quotation_net_amount CHECK ((net_payable_amount >= (0)::numeric))
);


--
-- Name: quotations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quotations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- Name: replacements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.replacements (
    id bigint NOT NULL,
    ticket_id bigint NOT NULL,
    original_serial_id bigint NOT NULL,
    replacement_serial_id bigint NOT NULL,
    replacement_reason text NOT NULL,
    replacement_date date NOT NULL,
    replaced_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_replacement_distinct_serials CHECK ((original_serial_id <> replacement_serial_id))
);


--
-- Name: replacements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.replacements_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: replacements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.replacements_id_seq OWNED BY public.replacements.id;


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    id bigint NOT NULL,
    role_id bigint NOT NULL,
    permission_id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.role_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    is_system_role boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: serial_number_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.serial_number_history (
    id bigint NOT NULL,
    serial_number_id bigint NOT NULL,
    previous_status character varying(50),
    new_status character varying(50) NOT NULL,
    project_id bigint,
    action_taken character varying(100) NOT NULL,
    recorded_by bigint NOT NULL,
    remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: serial_number_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.serial_number_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: serial_number_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.serial_number_history_id_seq OWNED BY public.serial_number_history.id;


--
-- Name: serial_numbers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.serial_numbers (
    id bigint NOT NULL,
    serial_number character varying(100) NOT NULL,
    product_id bigint NOT NULL,
    inventory_id bigint,
    purchase_order_id bigint,
    project_id bigint,
    supplier_id bigint,
    status character varying(50) NOT NULL,
    warranty_months bigint NOT NULL,
    received_date date NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_serial_warranty_months CHECK ((warranty_months >= 0))
);


--
-- Name: serial_numbers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.serial_numbers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: serial_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.serial_numbers_id_seq OWNED BY public.serial_numbers.id;


--
-- Name: service_ticket_confirmations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_ticket_confirmations (
    id bigint NOT NULL,
    ticket_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    resolution_confirmed boolean NOT NULL,
    customer_rating bigint,
    customer_feedback text,
    confirmed_at timestamp with time zone DEFAULT now() NOT NULL,
    confirmation_channel character varying(50) NOT NULL,
    signature_attachment_id bigint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_ticket_rating_range CHECK (((customer_rating IS NULL) OR ((customer_rating >= 1) AND (customer_rating <= 5))))
);


--
-- Name: service_ticket_confirmations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.service_ticket_confirmations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: service_ticket_confirmations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.service_ticket_confirmations_id_seq OWNED BY public.service_ticket_confirmations.id;


--
-- Name: service_tickets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_tickets (
    id bigint NOT NULL,
    ticket_number character varying(50) NOT NULL,
    project_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    serial_number_id bigint,
    warranty_record_id bigint,
    issue_category character varying(50) NOT NULL,
    priority character varying(50) NOT NULL,
    description text NOT NULL,
    status character varying(50) NOT NULL,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: service_tickets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.service_tickets_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: service_tickets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.service_tickets_id_seq OWNED BY public.service_tickets.id;


--
-- Name: service_visits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_visits (
    id bigint NOT NULL,
    ticket_id bigint NOT NULL,
    technician_id bigint NOT NULL,
    visit_number bigint NOT NULL,
    scheduled_date date NOT NULL,
    visit_status character varying(50) NOT NULL,
    actual_start timestamp with time zone,
    actual_end timestamp with time zone,
    findings text,
    action_taken text,
    parts_replaced boolean NOT NULL,
    customer_present_name character varying(150),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_service_visit_times CHECK (((actual_end IS NULL) OR (actual_start IS NULL) OR (actual_end >= actual_start)))
);


--
-- Name: service_visits_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.service_visits_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: service_visits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.service_visits_id_seq OWNED BY public.service_visits.id;


--
-- Name: skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skills (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(100) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: skills_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.skills_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: skills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.skills_id_seq OWNED BY public.skills.id;


--
-- Name: stock_movements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stock_movements (
    id bigint NOT NULL,
    inventory_id bigint NOT NULL,
    product_id bigint NOT NULL,
    movement_type character varying(50) NOT NULL,
    reference_type character varying(50) NOT NULL,
    reference_id bigint,
    quantity numeric(10,2) NOT NULL,
    unit_cost numeric(12,2) NOT NULL,
    quantity_before numeric(12,2) NOT NULL,
    quantity_after numeric(12,2) NOT NULL,
    performed_by bigint NOT NULL,
    remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_stock_mov_q_after_non_negative CHECK ((quantity_after >= (0)::numeric)),
    CONSTRAINT chk_stock_mov_q_before_non_negative CHECK ((quantity_before >= (0)::numeric))
);


--
-- Name: stock_movements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stock_movements_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: stock_movements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stock_movements_id_seq OWNED BY public.stock_movements.id;


--
-- Name: stock_reservations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stock_reservations (
    id bigint NOT NULL,
    inventory_id bigint NOT NULL,
    product_id bigint NOT NULL,
    project_id bigint NOT NULL,
    reserved_quantity numeric(10,2) NOT NULL,
    status character varying(50) NOT NULL,
    reserved_by bigint NOT NULL,
    expiry_date date,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_stock_res_qty_positive CHECK ((reserved_quantity > (0)::numeric))
);


--
-- Name: stock_reservations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stock_reservations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: stock_reservations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stock_reservations_id_seq OWNED BY public.stock_reservations.id;


--
-- Name: subsidy_applications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subsidy_applications (
    id bigint NOT NULL,
    application_number character varying(50) NOT NULL,
    project_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    portal_registration_number character varying(100),
    discom_name character varying(150) NOT NULL,
    sanctioned_capacity_kw numeric(5,2) NOT NULL,
    eligible_subsidy_amount numeric(12,2) NOT NULL,
    application_date date NOT NULL,
    status character varying(50) NOT NULL,
    rejection_reason text,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_subsidy_amount_non_negative CHECK ((eligible_subsidy_amount >= (0)::numeric)),
    CONSTRAINT chk_subsidy_capacity_positive CHECK ((sanctioned_capacity_kw > (0)::numeric))
);


--
-- Name: subsidy_applications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subsidy_applications_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subsidy_applications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subsidy_applications_id_seq OWNED BY public.subsidy_applications.id;


--
-- Name: subsidy_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subsidy_documents (
    id bigint NOT NULL,
    subsidy_application_id bigint NOT NULL,
    document_type character varying(100) NOT NULL,
    attachment_id bigint NOT NULL,
    verification_status character varying(50) NOT NULL,
    remarks text,
    verified_by bigint,
    verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: subsidy_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subsidy_documents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subsidy_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subsidy_documents_id_seq OWNED BY public.subsidy_documents.id;


--
-- Name: subsidy_payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subsidy_payments (
    id bigint NOT NULL,
    subsidy_application_id bigint NOT NULL,
    project_id bigint NOT NULL,
    payment_reference character varying(100) NOT NULL,
    disbursement_date date NOT NULL,
    disbursed_amount numeric(12,2) NOT NULL,
    bank_reference_number character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_subsidy_payment_amount_positive CHECK ((disbursed_amount > (0)::numeric))
);


--
-- Name: subsidy_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subsidy_payments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subsidy_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subsidy_payments_id_seq OWNED BY public.subsidy_payments.id;


--
-- Name: subsidy_status_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subsidy_status_history (
    id bigint NOT NULL,
    subsidy_application_id bigint NOT NULL,
    previous_status character varying(50),
    new_status character varying(50) NOT NULL,
    action_date timestamp with time zone DEFAULT now() NOT NULL,
    comments text,
    updated_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: subsidy_status_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subsidy_status_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subsidy_status_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subsidy_status_history_id_seq OWNED BY public.subsidy_status_history.id;


--
-- Name: supplier_invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.supplier_invoices (
    id bigint NOT NULL,
    invoice_number character varying(100) NOT NULL,
    purchase_order_id bigint NOT NULL,
    supplier_id bigint NOT NULL,
    invoice_date date NOT NULL,
    due_date date NOT NULL,
    subtotal numeric(12,2) NOT NULL,
    tax_amount numeric(12,2) NOT NULL,
    total_amount numeric(12,2) NOT NULL,
    paid_amount numeric(12,2) NOT NULL,
    balance_amount numeric(12,2) NOT NULL,
    payment_status character varying(50) NOT NULL,
    attachment_id bigint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_supplier_invoice_balance CHECK ((balance_amount >= (0)::numeric)),
    CONSTRAINT chk_supplier_invoice_dates CHECK ((due_date >= invoice_date)),
    CONSTRAINT chk_supplier_invoice_paid CHECK ((paid_amount >= (0)::numeric)),
    CONSTRAINT chk_supplier_invoice_total CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: supplier_invoices_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.supplier_invoices_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: supplier_invoices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.supplier_invoices_id_seq OWNED BY public.supplier_invoices.id;


--
-- Name: supplier_payment_allocations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.supplier_payment_allocations (
    id bigint NOT NULL,
    supplier_payment_id bigint NOT NULL,
    supplier_invoice_id bigint NOT NULL,
    allocated_amount numeric(12,2) NOT NULL,
    allocated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_supplier_alloc_amount_positive CHECK ((allocated_amount > (0)::numeric))
);


--
-- Name: supplier_payment_allocations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.supplier_payment_allocations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: supplier_payment_allocations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.supplier_payment_allocations_id_seq OWNED BY public.supplier_payment_allocations.id;


--
-- Name: supplier_payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.supplier_payments (
    id bigint NOT NULL,
    payment_reference character varying(100) NOT NULL,
    supplier_id bigint NOT NULL,
    payment_date date NOT NULL,
    payment_mode character varying(50) NOT NULL,
    amount numeric(12,2) NOT NULL,
    unallocated_amount numeric(12,2) NOT NULL,
    status character varying(50) NOT NULL,
    notes text,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_supplier_payment_amount_positive CHECK ((amount > (0)::numeric)),
    CONSTRAINT chk_supplier_payment_unallocated_le_total CHECK ((unallocated_amount <= amount)),
    CONSTRAINT chk_supplier_payment_unallocated_non_negative CHECK ((unallocated_amount >= (0)::numeric))
);


--
-- Name: supplier_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.supplier_payments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: supplier_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.supplier_payments_id_seq OWNED BY public.supplier_payments.id;


--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.suppliers (
    id bigint NOT NULL,
    supplier_code character varying(50) NOT NULL,
    company_name character varying(255) NOT NULL,
    contact_person character varying(150) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(30) NOT NULL,
    address text NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    gst_number character varying(30),
    pan_number character varying(20),
    bank_account_details text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: suppliers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.suppliers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: suppliers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.suppliers_id_seq OWNED BY public.suppliers.id;


--
-- Name: survey_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.survey_approvals (
    id bigint NOT NULL,
    survey_id bigint NOT NULL,
    reviewer_id bigint NOT NULL,
    action character varying(50) NOT NULL,
    comments text NOT NULL,
    revision_number bigint NOT NULL,
    reviewed_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: survey_approvals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.survey_approvals_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: survey_approvals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.survey_approvals_id_seq OWNED BY public.survey_approvals.id;


--
-- Name: surveys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.surveys (
    id bigint NOT NULL,
    enquiry_id bigint NOT NULL,
    surveyor_id bigint NOT NULL,
    survey_number character varying(50) NOT NULL,
    scheduled_at timestamp with time zone NOT NULL,
    conducted_at timestamp with time zone,
    roof_area_sqft numeric(10,2),
    shadow_free_area_sqft numeric(10,2),
    roof_orientation character varying(50),
    roof_tilt_degrees numeric(4,1),
    roof_structure_type character varying(100),
    existing_phase character varying(50) NOT NULL,
    sanctioned_load_kw numeric(6,2),
    gps_latitude numeric(10,7),
    gps_longitude numeric(10,7),
    technical_feasibility character varying(50) NOT NULL,
    remarks text,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_survey_roof_area CHECK (((roof_area_sqft IS NULL) OR (roof_area_sqft >= (0)::numeric))),
    CONSTRAINT chk_survey_shadow_area CHECK (((shadow_free_area_sqft IS NULL) OR (shadow_free_area_sqft >= (0)::numeric)))
);


--
-- Name: surveys_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.surveys_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: surveys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.surveys_id_seq OWNED BY public.surveys.id;


--
-- Name: task_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task_assignments (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    assigned_by bigint NOT NULL,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(50) NOT NULL,
    remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: task_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_assignments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_assignments_id_seq OWNED BY public.task_assignments.id;


--
-- Name: task_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task_history (
    id bigint NOT NULL,
    task_id bigint NOT NULL,
    previous_status character varying(50),
    new_status character varying(50) NOT NULL,
    comment text,
    changed_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: task_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_history_id_seq OWNED BY public.task_history.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    id bigint NOT NULL,
    task_code character varying(50) NOT NULL,
    project_id bigint,
    title character varying(255) NOT NULL,
    description text,
    task_type character varying(50) NOT NULL,
    priority character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    due_date date,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tasks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: technician_payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.technician_payments (
    id bigint NOT NULL,
    payment_reference character varying(50) NOT NULL,
    employee_id bigint NOT NULL,
    installation_id bigint,
    payment_type character varying(50) NOT NULL,
    amount numeric(12,2) NOT NULL,
    payment_date date NOT NULL,
    status character varying(50) NOT NULL,
    approved_by bigint,
    remarks text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_tech_payment_amount_positive CHECK ((amount > (0)::numeric))
);


--
-- Name: technician_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.technician_payments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: technician_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.technician_payments_id_seq OWNED BY public.technician_payments.id;


--
-- Name: technician_worklogs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.technician_worklogs (
    id bigint NOT NULL,
    installation_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    work_date date NOT NULL,
    hours_worked numeric(4,2) NOT NULL,
    work_description text NOT NULL,
    approved_by bigint,
    approved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_worklog_hours_valid CHECK (((hours_worked > (0)::numeric) AND (hours_worked <= (24)::numeric)))
);


--
-- Name: technician_worklogs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.technician_worklogs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: technician_worklogs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.technician_worklogs_id_seq OWNED BY public.technician_worklogs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    role_id bigint NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(30),
    full_name character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: warranty_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.warranty_events (
    id bigint NOT NULL,
    warranty_record_id bigint NOT NULL,
    event_type character varying(50) NOT NULL,
    event_date timestamp with time zone DEFAULT now() NOT NULL,
    description text NOT NULL,
    recorded_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: warranty_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warranty_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warranty_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.warranty_events_id_seq OWNED BY public.warranty_events.id;


--
-- Name: warranty_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.warranty_policies (
    id bigint NOT NULL,
    policy_code character varying(50) NOT NULL,
    name character varying(150) NOT NULL,
    product_id bigint,
    warranty_period_months bigint NOT NULL,
    activation_trigger character varying(50) NOT NULL,
    terms_and_conditions text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_warranty_period_positive CHECK ((warranty_period_months > 0))
);


--
-- Name: warranty_policies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warranty_policies_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warranty_policies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.warranty_policies_id_seq OWNED BY public.warranty_policies.id;


--
-- Name: warranty_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.warranty_records (
    id bigint NOT NULL,
    certificate_number character varying(100) NOT NULL,
    project_id bigint NOT NULL,
    product_id bigint NOT NULL,
    serial_number_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    warranty_policy_id bigint NOT NULL,
    delivery_date date NOT NULL,
    activation_trigger character varying(50) NOT NULL,
    activation_date date,
    warranty_start_date date NOT NULL,
    warranty_end_date date NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_warranty_dates CHECK ((warranty_end_date >= warranty_start_date))
);


--
-- Name: warranty_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warranty_records_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warranty_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.warranty_records_id_seq OWNED BY public.warranty_records.id;


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: bom_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_items ALTER COLUMN id SET DEFAULT nextval('public.bom_items_id_seq'::regclass);


--
-- Name: bom_templates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_templates ALTER COLUMN id SET DEFAULT nextval('public.bom_templates_id_seq'::regclass);


--
-- Name: customer_acceptances id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_acceptances ALTER COLUMN id SET DEFAULT nextval('public.customer_acceptances_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);


--
-- Name: delivery_confirmations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_confirmations ALTER COLUMN id SET DEFAULT nextval('public.delivery_confirmations_id_seq'::regclass);


--
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- Name: dispatch_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_items ALTER COLUMN id SET DEFAULT nextval('public.dispatch_items_id_seq'::regclass);


--
-- Name: dispatch_serials id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_serials ALTER COLUMN id SET DEFAULT nextval('public.dispatch_serials_id_seq'::regclass);


--
-- Name: dispatches id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatches ALTER COLUMN id SET DEFAULT nextval('public.dispatches_id_seq'::regclass);


--
-- Name: employee_certifications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_certifications ALTER COLUMN id SET DEFAULT nextval('public.employee_certifications_id_seq'::regclass);


--
-- Name: employee_skills id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills ALTER COLUMN id SET DEFAULT nextval('public.employee_skills_id_seq'::regclass);


--
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- Name: enquiries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enquiries ALTER COLUMN id SET DEFAULT nextval('public.enquiries_id_seq'::regclass);


--
-- Name: escalations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalations ALTER COLUMN id SET DEFAULT nextval('public.escalations_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- Name: file_attachments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_attachments ALTER COLUMN id SET DEFAULT nextval('public.file_attachments_id_seq'::regclass);


--
-- Name: followups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.followups ALTER COLUMN id SET DEFAULT nextval('public.followups_id_seq'::regclass);


--
-- Name: goods_receipt_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipt_items ALTER COLUMN id SET DEFAULT nextval('public.goods_receipt_items_id_seq'::regclass);


--
-- Name: goods_receipts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipts ALTER COLUMN id SET DEFAULT nextval('public.goods_receipts_id_seq'::regclass);


--
-- Name: installation_checklists id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_checklists ALTER COLUMN id SET DEFAULT nextval('public.installation_checklists_id_seq'::regclass);


--
-- Name: installation_photos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_photos ALTER COLUMN id SET DEFAULT nextval('public.installation_photos_id_seq'::regclass);


--
-- Name: installation_schedule_technicians id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedule_technicians ALTER COLUMN id SET DEFAULT nextval('public.installation_schedule_technicians_id_seq'::regclass);


--
-- Name: installation_schedules id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedules ALTER COLUMN id SET DEFAULT nextval('public.installation_schedules_id_seq'::regclass);


--
-- Name: installation_tests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_tests ALTER COLUMN id SET DEFAULT nextval('public.installation_tests_id_seq'::regclass);


--
-- Name: installations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installations ALTER COLUMN id SET DEFAULT nextval('public.installations_id_seq'::regclass);


--
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- Name: invoice_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice_items ALTER COLUMN id SET DEFAULT nextval('public.invoice_items_id_seq'::regclass);


--
-- Name: invoices id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices ALTER COLUMN id SET DEFAULT nextval('public.invoices_id_seq'::regclass);


--
-- Name: material_consumption id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_consumption ALTER COLUMN id SET DEFAULT nextval('public.material_consumption_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: payment_allocations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_allocations ALTER COLUMN id SET DEFAULT nextval('public.payment_allocations_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: project_bom_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_bom_items ALTER COLUMN id SET DEFAULT nextval('public.project_bom_items_id_seq'::regclass);


--
-- Name: project_costs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_costs ALTER COLUMN id SET DEFAULT nextval('public.project_costs_id_seq'::regclass);


--
-- Name: project_notes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_notes ALTER COLUMN id SET DEFAULT nextval('public.project_notes_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: purchase_order_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items ALTER COLUMN id SET DEFAULT nextval('public.purchase_order_items_id_seq'::regclass);


--
-- Name: purchase_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN id SET DEFAULT nextval('public.purchase_orders_id_seq'::regclass);


--
-- Name: quotation_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_items ALTER COLUMN id SET DEFAULT nextval('public.quotation_items_id_seq'::regclass);


--
-- Name: quotation_revisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_revisions ALTER COLUMN id SET DEFAULT nextval('public.quotation_revisions_id_seq'::regclass);


--
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- Name: replacements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replacements ALTER COLUMN id SET DEFAULT nextval('public.replacements_id_seq'::regclass);


--
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: serial_number_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_number_history ALTER COLUMN id SET DEFAULT nextval('public.serial_number_history_id_seq'::regclass);


--
-- Name: serial_numbers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_numbers ALTER COLUMN id SET DEFAULT nextval('public.serial_numbers_id_seq'::regclass);


--
-- Name: service_ticket_confirmations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_ticket_confirmations ALTER COLUMN id SET DEFAULT nextval('public.service_ticket_confirmations_id_seq'::regclass);


--
-- Name: service_tickets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_tickets ALTER COLUMN id SET DEFAULT nextval('public.service_tickets_id_seq'::regclass);


--
-- Name: service_visits id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_visits ALTER COLUMN id SET DEFAULT nextval('public.service_visits_id_seq'::regclass);


--
-- Name: skills id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills ALTER COLUMN id SET DEFAULT nextval('public.skills_id_seq'::regclass);


--
-- Name: stock_movements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_movements ALTER COLUMN id SET DEFAULT nextval('public.stock_movements_id_seq'::regclass);


--
-- Name: stock_reservations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_reservations ALTER COLUMN id SET DEFAULT nextval('public.stock_reservations_id_seq'::regclass);


--
-- Name: subsidy_applications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_applications ALTER COLUMN id SET DEFAULT nextval('public.subsidy_applications_id_seq'::regclass);


--
-- Name: subsidy_documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_documents ALTER COLUMN id SET DEFAULT nextval('public.subsidy_documents_id_seq'::regclass);


--
-- Name: subsidy_payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_payments ALTER COLUMN id SET DEFAULT nextval('public.subsidy_payments_id_seq'::regclass);


--
-- Name: subsidy_status_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_status_history ALTER COLUMN id SET DEFAULT nextval('public.subsidy_status_history_id_seq'::regclass);


--
-- Name: supplier_invoices id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_invoices ALTER COLUMN id SET DEFAULT nextval('public.supplier_invoices_id_seq'::regclass);


--
-- Name: supplier_payment_allocations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payment_allocations ALTER COLUMN id SET DEFAULT nextval('public.supplier_payment_allocations_id_seq'::regclass);


--
-- Name: supplier_payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payments ALTER COLUMN id SET DEFAULT nextval('public.supplier_payments_id_seq'::regclass);


--
-- Name: suppliers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers ALTER COLUMN id SET DEFAULT nextval('public.suppliers_id_seq'::regclass);


--
-- Name: survey_approvals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_approvals ALTER COLUMN id SET DEFAULT nextval('public.survey_approvals_id_seq'::regclass);


--
-- Name: surveys id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surveys ALTER COLUMN id SET DEFAULT nextval('public.surveys_id_seq'::regclass);


--
-- Name: task_assignments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_assignments ALTER COLUMN id SET DEFAULT nextval('public.task_assignments_id_seq'::regclass);


--
-- Name: task_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_history ALTER COLUMN id SET DEFAULT nextval('public.task_history_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: technician_payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_payments ALTER COLUMN id SET DEFAULT nextval('public.technician_payments_id_seq'::regclass);


--
-- Name: technician_worklogs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_worklogs ALTER COLUMN id SET DEFAULT nextval('public.technician_worklogs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: warranty_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_events ALTER COLUMN id SET DEFAULT nextval('public.warranty_events_id_seq'::regclass);


--
-- Name: warranty_policies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_policies ALTER COLUMN id SET DEFAULT nextval('public.warranty_policies_id_seq'::regclass);


--
-- Name: warranty_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_records ALTER COLUMN id SET DEFAULT nextval('public.warranty_records_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: bom_items bom_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_items
    ADD CONSTRAINT bom_items_pkey PRIMARY KEY (id);


--
-- Name: bom_templates bom_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_templates
    ADD CONSTRAINT bom_templates_pkey PRIMARY KEY (id);


--
-- Name: bom_templates bom_templates_template_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_templates
    ADD CONSTRAINT bom_templates_template_name_key UNIQUE (template_name);


--
-- Name: customer_acceptances customer_acceptances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_acceptances
    ADD CONSTRAINT customer_acceptances_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: delivery_confirmations delivery_confirmations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_confirmations
    ADD CONSTRAINT delivery_confirmations_pkey PRIMARY KEY (id);


--
-- Name: departments departments_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_name_key UNIQUE (name);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: dispatch_items dispatch_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_items
    ADD CONSTRAINT dispatch_items_pkey PRIMARY KEY (id);


--
-- Name: dispatch_serials dispatch_serials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_serials
    ADD CONSTRAINT dispatch_serials_pkey PRIMARY KEY (id);


--
-- Name: dispatches dispatches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatches
    ADD CONSTRAINT dispatches_pkey PRIMARY KEY (id);


--
-- Name: employee_certifications employee_certifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_certifications
    ADD CONSTRAINT employee_certifications_pkey PRIMARY KEY (id);


--
-- Name: employee_skills employee_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_pkey PRIMARY KEY (id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: enquiries enquiries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enquiries
    ADD CONSTRAINT enquiries_pkey PRIMARY KEY (id);


--
-- Name: escalations escalations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalations
    ADD CONSTRAINT escalations_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: file_attachments file_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_attachments
    ADD CONSTRAINT file_attachments_pkey PRIMARY KEY (id);


--
-- Name: followups followups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.followups
    ADD CONSTRAINT followups_pkey PRIMARY KEY (id);


--
-- Name: goods_receipt_items goods_receipt_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT goods_receipt_items_pkey PRIMARY KEY (id);


--
-- Name: goods_receipts goods_receipts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT goods_receipts_pkey PRIMARY KEY (id);


--
-- Name: installation_checklists installation_checklists_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_checklists
    ADD CONSTRAINT installation_checklists_pkey PRIMARY KEY (id);


--
-- Name: installation_photos installation_photos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_photos
    ADD CONSTRAINT installation_photos_pkey PRIMARY KEY (id);


--
-- Name: installation_schedule_technicians installation_schedule_technicians_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedule_technicians
    ADD CONSTRAINT installation_schedule_technicians_pkey PRIMARY KEY (id);


--
-- Name: installation_schedules installation_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedules
    ADD CONSTRAINT installation_schedules_pkey PRIMARY KEY (id);


--
-- Name: installation_tests installation_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_tests
    ADD CONSTRAINT installation_tests_pkey PRIMARY KEY (id);


--
-- Name: installations installations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installations
    ADD CONSTRAINT installations_pkey PRIMARY KEY (id);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- Name: invoice_items invoice_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice_items
    ADD CONSTRAINT invoice_items_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: material_consumption material_consumption_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_consumption
    ADD CONSTRAINT material_consumption_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payment_allocations payment_allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_allocations
    ADD CONSTRAINT payment_allocations_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: project_bom_items project_bom_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_bom_items
    ADD CONSTRAINT project_bom_items_pkey PRIMARY KEY (id);


--
-- Name: project_costs project_costs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_costs
    ADD CONSTRAINT project_costs_pkey PRIMARY KEY (id);


--
-- Name: project_notes project_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_notes
    ADD CONSTRAINT project_notes_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: purchase_order_items purchase_order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT purchase_order_items_pkey PRIMARY KEY (id);


--
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (id);


--
-- Name: quotation_items quotation_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_items
    ADD CONSTRAINT quotation_items_pkey PRIMARY KEY (id);


--
-- Name: quotation_revisions quotation_revisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_revisions
    ADD CONSTRAINT quotation_revisions_pkey PRIMARY KEY (id);


--
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);


--
-- Name: replacements replacements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replacements
    ADD CONSTRAINT replacements_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: serial_number_history serial_number_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_number_history
    ADD CONSTRAINT serial_number_history_pkey PRIMARY KEY (id);


--
-- Name: serial_numbers serial_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_numbers
    ADD CONSTRAINT serial_numbers_pkey PRIMARY KEY (id);


--
-- Name: service_ticket_confirmations service_ticket_confirmations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_ticket_confirmations
    ADD CONSTRAINT service_ticket_confirmations_pkey PRIMARY KEY (id);


--
-- Name: service_tickets service_tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_tickets
    ADD CONSTRAINT service_tickets_pkey PRIMARY KEY (id);


--
-- Name: service_visits service_visits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_visits
    ADD CONSTRAINT service_visits_pkey PRIMARY KEY (id);


--
-- Name: skills skills_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_name_key UNIQUE (name);


--
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (id);


--
-- Name: stock_movements stock_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_pkey PRIMARY KEY (id);


--
-- Name: stock_reservations stock_reservations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_reservations
    ADD CONSTRAINT stock_reservations_pkey PRIMARY KEY (id);


--
-- Name: subsidy_applications subsidy_applications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_applications
    ADD CONSTRAINT subsidy_applications_pkey PRIMARY KEY (id);


--
-- Name: subsidy_documents subsidy_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_documents
    ADD CONSTRAINT subsidy_documents_pkey PRIMARY KEY (id);


--
-- Name: subsidy_payments subsidy_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_payments
    ADD CONSTRAINT subsidy_payments_pkey PRIMARY KEY (id);


--
-- Name: subsidy_status_history subsidy_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_status_history
    ADD CONSTRAINT subsidy_status_history_pkey PRIMARY KEY (id);


--
-- Name: supplier_invoices supplier_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT supplier_invoices_pkey PRIMARY KEY (id);


--
-- Name: supplier_payment_allocations supplier_payment_allocations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payment_allocations
    ADD CONSTRAINT supplier_payment_allocations_pkey PRIMARY KEY (id);


--
-- Name: supplier_payments supplier_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payments
    ADD CONSTRAINT supplier_payments_pkey PRIMARY KEY (id);


--
-- Name: suppliers suppliers_gst_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_gst_number_key UNIQUE (gst_number);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);


--
-- Name: survey_approvals survey_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_approvals
    ADD CONSTRAINT survey_approvals_pkey PRIMARY KEY (id);


--
-- Name: surveys surveys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surveys
    ADD CONSTRAINT surveys_pkey PRIMARY KEY (id);


--
-- Name: task_assignments task_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_assignments
    ADD CONSTRAINT task_assignments_pkey PRIMARY KEY (id);


--
-- Name: task_history task_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_history
    ADD CONSTRAINT task_history_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: technician_payments technician_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_payments
    ADD CONSTRAINT technician_payments_pkey PRIMARY KEY (id);


--
-- Name: technician_worklogs technician_worklogs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_worklogs
    ADD CONSTRAINT technician_worklogs_pkey PRIMARY KEY (id);


--
-- Name: bom_items uq_bom_template_product; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_items
    ADD CONSTRAINT uq_bom_template_product UNIQUE (bom_template_id, product_id);


--
-- Name: dispatch_serials uq_dispatch_item_serial; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_serials
    ADD CONSTRAINT uq_dispatch_item_serial UNIQUE (dispatch_item_id, serial_number_id);


--
-- Name: employee_skills uq_employee_skill; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT uq_employee_skill UNIQUE (employee_id, skill_id);


--
-- Name: project_bom_items uq_project_bom_product; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_bom_items
    ADD CONSTRAINT uq_project_bom_product UNIQUE (project_id, product_id);


--
-- Name: quotation_revisions uq_quotation_revision; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_revisions
    ADD CONSTRAINT uq_quotation_revision UNIQUE (quotation_id, revision_number);


--
-- Name: role_permissions uq_role_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id);


--
-- Name: installation_schedule_technicians uq_schedule_technician; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedule_technicians
    ADD CONSTRAINT uq_schedule_technician UNIQUE (schedule_id, employee_id);


--
-- Name: supplier_invoices uq_supplier_invoice_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT uq_supplier_invoice_number UNIQUE (supplier_id, invoice_number);


--
-- Name: task_assignments uq_task_employee_assignment; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_assignments
    ADD CONSTRAINT uq_task_employee_assignment UNIQUE (task_id, employee_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: warranty_events warranty_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_events
    ADD CONSTRAINT warranty_events_pkey PRIMARY KEY (id);


--
-- Name: warranty_policies warranty_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_policies
    ADD CONSTRAINT warranty_policies_pkey PRIMARY KEY (id);


--
-- Name: warranty_records warranty_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_records
    ADD CONSTRAINT warranty_records_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_logs_action_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_action_entity ON public.audit_logs USING btree (action, entity_name);


--
-- Name: idx_employee_skills_emp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_skills_emp ON public.employee_skills USING btree (employee_id);


--
-- Name: idx_employee_skills_skill; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_skills_skill ON public.employee_skills USING btree (skill_id);


--
-- Name: idx_file_attachment_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_file_attachment_entity ON public.file_attachments USING btree (entity_type, entity_id);


--
-- Name: idx_pay_alloc_pair; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pay_alloc_pair ON public.payment_allocations USING btree (payment_id, invoice_id);


--
-- Name: idx_role_permissions_perm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_permissions_perm ON public.role_permissions USING btree (permission_id);


--
-- Name: idx_role_permissions_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_permissions_role ON public.role_permissions USING btree (role_id);


--
-- Name: idx_supp_alloc_pay_inv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_supp_alloc_pay_inv ON public.supplier_payment_allocations USING btree (supplier_payment_id, supplier_invoice_id);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_id ON public.audit_logs USING btree (entity_id);


--
-- Name: ix_audit_logs_entity_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_name ON public.audit_logs USING btree (entity_name);


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_bom_items_bom_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bom_items_bom_template_id ON public.bom_items USING btree (bom_template_id);


--
-- Name: ix_bom_items_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bom_items_product_id ON public.bom_items USING btree (product_id);


--
-- Name: ix_bom_templates_capacity_kw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bom_templates_capacity_kw ON public.bom_templates USING btree (capacity_kw);


--
-- Name: ix_bom_templates_system_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bom_templates_system_type ON public.bom_templates USING btree (system_type);


--
-- Name: ix_customer_acceptances_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customer_acceptances_customer_id ON public.customer_acceptances USING btree (customer_id);


--
-- Name: ix_customer_acceptances_installation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_customer_acceptances_installation_id ON public.customer_acceptances USING btree (installation_id);


--
-- Name: ix_customer_acceptances_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customer_acceptances_project_id ON public.customer_acceptances USING btree (project_id);


--
-- Name: ix_customers_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customers_city ON public.customers USING btree (city);


--
-- Name: ix_customers_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customers_email ON public.customers USING btree (email);


--
-- Name: ix_customers_full_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customers_full_name ON public.customers USING btree (full_name);


--
-- Name: ix_customers_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_customers_phone ON public.customers USING btree (phone);


--
-- Name: ix_customers_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_customers_user_id ON public.customers USING btree (user_id);


--
-- Name: ix_delivery_confirmations_dispatch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_delivery_confirmations_dispatch_id ON public.delivery_confirmations USING btree (dispatch_id);


--
-- Name: ix_delivery_confirmations_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_delivery_confirmations_project_id ON public.delivery_confirmations USING btree (project_id);


--
-- Name: ix_departments_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_departments_code ON public.departments USING btree (code);


--
-- Name: ix_dispatch_items_dispatch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dispatch_items_dispatch_id ON public.dispatch_items USING btree (dispatch_id);


--
-- Name: ix_dispatch_items_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dispatch_items_product_id ON public.dispatch_items USING btree (product_id);


--
-- Name: ix_dispatch_serials_dispatch_item_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dispatch_serials_dispatch_item_id ON public.dispatch_serials USING btree (dispatch_item_id);


--
-- Name: ix_dispatch_serials_serial_number_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dispatch_serials_serial_number_id ON public.dispatch_serials USING btree (serial_number_id);


--
-- Name: ix_dispatches_dispatch_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_dispatches_dispatch_number ON public.dispatches USING btree (dispatch_number);


--
-- Name: ix_dispatches_dispatch_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dispatches_dispatch_status ON public.dispatches USING btree (dispatch_status);


--
-- Name: ix_dispatches_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dispatches_order_id ON public.dispatches USING btree (order_id);


--
-- Name: ix_dispatches_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dispatches_project_id ON public.dispatches USING btree (project_id);


--
-- Name: ix_employee_certifications_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_certifications_employee_id ON public.employee_certifications USING btree (employee_id);


--
-- Name: ix_employees_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employees_department_id ON public.employees USING btree (department_id);


--
-- Name: ix_employees_employee_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_employees_employee_code ON public.employees USING btree (employee_code);


--
-- Name: ix_employees_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_employees_user_id ON public.employees USING btree (user_id);


--
-- Name: ix_enquiries_assigned_sales_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enquiries_assigned_sales_id ON public.enquiries USING btree (assigned_sales_id);


--
-- Name: ix_enquiries_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enquiries_customer_id ON public.enquiries USING btree (customer_id);


--
-- Name: ix_enquiries_enquiry_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_enquiries_enquiry_number ON public.enquiries USING btree (enquiry_number);


--
-- Name: ix_enquiries_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_enquiries_status ON public.enquiries USING btree (status);


--
-- Name: ix_escalations_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_escalations_project_id ON public.escalations USING btree (project_id);


--
-- Name: ix_escalations_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_escalations_task_id ON public.escalations USING btree (task_id);


--
-- Name: ix_expenses_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_department_id ON public.expenses USING btree (department_id);


--
-- Name: ix_expenses_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_employee_id ON public.expenses USING btree (employee_id);


--
-- Name: ix_expenses_expense_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_expenses_expense_number ON public.expenses USING btree (expense_number);


--
-- Name: ix_expenses_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expenses_project_id ON public.expenses USING btree (project_id);


--
-- Name: ix_file_attachments_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_file_attachments_entity_id ON public.file_attachments USING btree (entity_id);


--
-- Name: ix_file_attachments_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_file_attachments_entity_type ON public.file_attachments USING btree (entity_type);


--
-- Name: ix_followups_conducted_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_followups_conducted_by ON public.followups USING btree (conducted_by);


--
-- Name: ix_followups_enquiry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_followups_enquiry_id ON public.followups USING btree (enquiry_id);


--
-- Name: ix_goods_receipt_items_goods_receipt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_goods_receipt_items_goods_receipt_id ON public.goods_receipt_items USING btree (goods_receipt_id);


--
-- Name: ix_goods_receipt_items_po_item_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_goods_receipt_items_po_item_id ON public.goods_receipt_items USING btree (po_item_id);


--
-- Name: ix_goods_receipt_items_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_goods_receipt_items_product_id ON public.goods_receipt_items USING btree (product_id);


--
-- Name: ix_goods_receipts_grn_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_goods_receipts_grn_number ON public.goods_receipts USING btree (grn_number);


--
-- Name: ix_goods_receipts_purchase_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_goods_receipts_purchase_order_id ON public.goods_receipts USING btree (purchase_order_id);


--
-- Name: ix_goods_receipts_supplier_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_goods_receipts_supplier_id ON public.goods_receipts USING btree (supplier_id);


--
-- Name: ix_installation_checklists_installation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_checklists_installation_id ON public.installation_checklists USING btree (installation_id);


--
-- Name: ix_installation_photos_installation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_photos_installation_id ON public.installation_photos USING btree (installation_id);


--
-- Name: ix_installation_photos_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_photos_stage ON public.installation_photos USING btree (stage);


--
-- Name: ix_installation_schedule_technicians_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_schedule_technicians_employee_id ON public.installation_schedule_technicians USING btree (employee_id);


--
-- Name: ix_installation_schedule_technicians_schedule_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_schedule_technicians_schedule_id ON public.installation_schedule_technicians USING btree (schedule_id);


--
-- Name: ix_installation_schedules_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_schedules_project_id ON public.installation_schedules USING btree (project_id);


--
-- Name: ix_installation_schedules_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_schedules_status ON public.installation_schedules USING btree (status);


--
-- Name: ix_installation_tests_installation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installation_tests_installation_id ON public.installation_tests USING btree (installation_id);


--
-- Name: ix_installations_lead_technician_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installations_lead_technician_id ON public.installations USING btree (lead_technician_id);


--
-- Name: ix_installations_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_installations_project_id ON public.installations USING btree (project_id);


--
-- Name: ix_installations_schedule_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installations_schedule_id ON public.installations USING btree (schedule_id);


--
-- Name: ix_installations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_installations_status ON public.installations USING btree (status);


--
-- Name: ix_inventory_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_inventory_product_id ON public.inventory USING btree (product_id);


--
-- Name: ix_invoice_items_invoice_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_invoice_items_invoice_id ON public.invoice_items USING btree (invoice_id);


--
-- Name: ix_invoice_items_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_invoice_items_product_id ON public.invoice_items USING btree (product_id);


--
-- Name: ix_invoices_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_invoices_customer_id ON public.invoices USING btree (customer_id);


--
-- Name: ix_invoices_invoice_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_invoices_invoice_number ON public.invoices USING btree (invoice_number);


--
-- Name: ix_invoices_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_invoices_order_id ON public.invoices USING btree (order_id);


--
-- Name: ix_invoices_payment_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_invoices_payment_status ON public.invoices USING btree (payment_status);


--
-- Name: ix_invoices_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_invoices_project_id ON public.invoices USING btree (project_id);


--
-- Name: ix_material_consumption_installation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_material_consumption_installation_id ON public.material_consumption USING btree (installation_id);


--
-- Name: ix_material_consumption_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_material_consumption_product_id ON public.material_consumption USING btree (product_id);


--
-- Name: ix_material_consumption_serial_number_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_material_consumption_serial_number_id ON public.material_consumption USING btree (serial_number_id);


--
-- Name: ix_notifications_is_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_orders_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_customer_id ON public.orders USING btree (customer_id);


--
-- Name: ix_orders_order_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_orders_order_number ON public.orders USING btree (order_number);


--
-- Name: ix_orders_quotation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_orders_quotation_id ON public.orders USING btree (quotation_id);


--
-- Name: ix_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_orders_status ON public.orders USING btree (status);


--
-- Name: ix_payment_allocations_invoice_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payment_allocations_invoice_id ON public.payment_allocations USING btree (invoice_id);


--
-- Name: ix_payment_allocations_payment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payment_allocations_payment_id ON public.payment_allocations USING btree (payment_id);


--
-- Name: ix_payments_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_customer_id ON public.payments USING btree (customer_id);


--
-- Name: ix_payments_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_order_id ON public.payments USING btree (order_id);


--
-- Name: ix_payments_payment_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_payments_payment_number ON public.payments USING btree (payment_number);


--
-- Name: ix_payments_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_project_id ON public.payments USING btree (project_id);


--
-- Name: ix_payments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_status ON public.payments USING btree (status);


--
-- Name: ix_payments_transaction_reference; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_payments_transaction_reference ON public.payments USING btree (transaction_reference);


--
-- Name: ix_permissions_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_permissions_code ON public.permissions USING btree (code);


--
-- Name: ix_permissions_module; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permissions_module ON public.permissions USING btree (module);


--
-- Name: ix_products_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_products_category ON public.products USING btree (category);


--
-- Name: ix_products_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_products_name ON public.products USING btree (name);


--
-- Name: ix_products_product_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_products_product_code ON public.products USING btree (product_code);


--
-- Name: ix_project_bom_items_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_bom_items_product_id ON public.project_bom_items USING btree (product_id);


--
-- Name: ix_project_bom_items_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_bom_items_project_id ON public.project_bom_items USING btree (project_id);


--
-- Name: ix_project_costs_cost_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_costs_cost_category ON public.project_costs USING btree (cost_category);


--
-- Name: ix_project_costs_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_costs_project_id ON public.project_costs USING btree (project_id);


--
-- Name: ix_project_notes_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_notes_project_id ON public.project_notes USING btree (project_id);


--
-- Name: ix_projects_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_customer_id ON public.projects USING btree (customer_id);


--
-- Name: ix_projects_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_projects_order_id ON public.projects USING btree (order_id);


--
-- Name: ix_projects_project_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_projects_project_code ON public.projects USING btree (project_code);


--
-- Name: ix_projects_project_manager_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_project_manager_id ON public.projects USING btree (project_manager_id);


--
-- Name: ix_projects_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_status ON public.projects USING btree (status);


--
-- Name: ix_purchase_order_items_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_purchase_order_items_product_id ON public.purchase_order_items USING btree (product_id);


--
-- Name: ix_purchase_order_items_purchase_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_purchase_order_items_purchase_order_id ON public.purchase_order_items USING btree (purchase_order_id);


--
-- Name: ix_purchase_orders_po_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_purchase_orders_po_number ON public.purchase_orders USING btree (po_number);


--
-- Name: ix_purchase_orders_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_purchase_orders_project_id ON public.purchase_orders USING btree (project_id);


--
-- Name: ix_purchase_orders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_purchase_orders_status ON public.purchase_orders USING btree (status);


--
-- Name: ix_purchase_orders_supplier_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_purchase_orders_supplier_id ON public.purchase_orders USING btree (supplier_id);


--
-- Name: ix_quotation_items_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quotation_items_product_id ON public.quotation_items USING btree (product_id);


--
-- Name: ix_quotation_items_quotation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quotation_items_quotation_id ON public.quotation_items USING btree (quotation_id);


--
-- Name: ix_quotation_revisions_quotation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quotation_revisions_quotation_id ON public.quotation_revisions USING btree (quotation_id);


--
-- Name: ix_quotations_enquiry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quotations_enquiry_id ON public.quotations USING btree (enquiry_id);


--
-- Name: ix_quotations_quotation_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_quotations_quotation_number ON public.quotations USING btree (quotation_number);


--
-- Name: ix_quotations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quotations_status ON public.quotations USING btree (status);


--
-- Name: ix_quotations_survey_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quotations_survey_id ON public.quotations USING btree (survey_id);


--
-- Name: ix_replacements_original_serial_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_replacements_original_serial_id ON public.replacements USING btree (original_serial_id);


--
-- Name: ix_replacements_replacement_serial_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_replacements_replacement_serial_id ON public.replacements USING btree (replacement_serial_id);


--
-- Name: ix_replacements_ticket_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_replacements_ticket_id ON public.replacements USING btree (ticket_id);


--
-- Name: ix_roles_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_roles_slug ON public.roles USING btree (slug);


--
-- Name: ix_serial_number_history_serial_number_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_serial_number_history_serial_number_id ON public.serial_number_history USING btree (serial_number_id);


--
-- Name: ix_serial_numbers_inventory_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_serial_numbers_inventory_id ON public.serial_numbers USING btree (inventory_id);


--
-- Name: ix_serial_numbers_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_serial_numbers_product_id ON public.serial_numbers USING btree (product_id);


--
-- Name: ix_serial_numbers_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_serial_numbers_project_id ON public.serial_numbers USING btree (project_id);


--
-- Name: ix_serial_numbers_serial_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_serial_numbers_serial_number ON public.serial_numbers USING btree (serial_number);


--
-- Name: ix_serial_numbers_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_serial_numbers_status ON public.serial_numbers USING btree (status);


--
-- Name: ix_service_ticket_confirmations_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_ticket_confirmations_customer_id ON public.service_ticket_confirmations USING btree (customer_id);


--
-- Name: ix_service_ticket_confirmations_ticket_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_service_ticket_confirmations_ticket_id ON public.service_ticket_confirmations USING btree (ticket_id);


--
-- Name: ix_service_tickets_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_tickets_customer_id ON public.service_tickets USING btree (customer_id);


--
-- Name: ix_service_tickets_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_tickets_project_id ON public.service_tickets USING btree (project_id);


--
-- Name: ix_service_tickets_serial_number_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_tickets_serial_number_id ON public.service_tickets USING btree (serial_number_id);


--
-- Name: ix_service_tickets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_tickets_status ON public.service_tickets USING btree (status);


--
-- Name: ix_service_tickets_ticket_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_service_tickets_ticket_number ON public.service_tickets USING btree (ticket_number);


--
-- Name: ix_service_tickets_warranty_record_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_tickets_warranty_record_id ON public.service_tickets USING btree (warranty_record_id);


--
-- Name: ix_service_visits_technician_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_visits_technician_id ON public.service_visits USING btree (technician_id);


--
-- Name: ix_service_visits_ticket_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_visits_ticket_id ON public.service_visits USING btree (ticket_id);


--
-- Name: ix_skills_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_skills_category ON public.skills USING btree (category);


--
-- Name: ix_stock_movements_inventory_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stock_movements_inventory_id ON public.stock_movements USING btree (inventory_id);


--
-- Name: ix_stock_movements_movement_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stock_movements_movement_type ON public.stock_movements USING btree (movement_type);


--
-- Name: ix_stock_movements_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stock_movements_product_id ON public.stock_movements USING btree (product_id);


--
-- Name: ix_stock_reservations_inventory_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stock_reservations_inventory_id ON public.stock_reservations USING btree (inventory_id);


--
-- Name: ix_stock_reservations_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stock_reservations_product_id ON public.stock_reservations USING btree (product_id);


--
-- Name: ix_stock_reservations_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stock_reservations_project_id ON public.stock_reservations USING btree (project_id);


--
-- Name: ix_stock_reservations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stock_reservations_status ON public.stock_reservations USING btree (status);


--
-- Name: ix_subsidy_applications_application_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_subsidy_applications_application_number ON public.subsidy_applications USING btree (application_number);


--
-- Name: ix_subsidy_applications_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subsidy_applications_customer_id ON public.subsidy_applications USING btree (customer_id);


--
-- Name: ix_subsidy_applications_portal_registration_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_subsidy_applications_portal_registration_number ON public.subsidy_applications USING btree (portal_registration_number);


--
-- Name: ix_subsidy_applications_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_subsidy_applications_project_id ON public.subsidy_applications USING btree (project_id);


--
-- Name: ix_subsidy_applications_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subsidy_applications_status ON public.subsidy_applications USING btree (status);


--
-- Name: ix_subsidy_documents_subsidy_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subsidy_documents_subsidy_application_id ON public.subsidy_documents USING btree (subsidy_application_id);


--
-- Name: ix_subsidy_payments_payment_reference; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_subsidy_payments_payment_reference ON public.subsidy_payments USING btree (payment_reference);


--
-- Name: ix_subsidy_payments_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subsidy_payments_project_id ON public.subsidy_payments USING btree (project_id);


--
-- Name: ix_subsidy_payments_subsidy_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subsidy_payments_subsidy_application_id ON public.subsidy_payments USING btree (subsidy_application_id);


--
-- Name: ix_subsidy_status_history_subsidy_application_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subsidy_status_history_subsidy_application_id ON public.subsidy_status_history USING btree (subsidy_application_id);


--
-- Name: ix_supplier_invoices_invoice_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_invoices_invoice_number ON public.supplier_invoices USING btree (invoice_number);


--
-- Name: ix_supplier_invoices_payment_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_invoices_payment_status ON public.supplier_invoices USING btree (payment_status);


--
-- Name: ix_supplier_invoices_purchase_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_invoices_purchase_order_id ON public.supplier_invoices USING btree (purchase_order_id);


--
-- Name: ix_supplier_invoices_supplier_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_invoices_supplier_id ON public.supplier_invoices USING btree (supplier_id);


--
-- Name: ix_supplier_payment_allocations_supplier_invoice_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_payment_allocations_supplier_invoice_id ON public.supplier_payment_allocations USING btree (supplier_invoice_id);


--
-- Name: ix_supplier_payment_allocations_supplier_payment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_payment_allocations_supplier_payment_id ON public.supplier_payment_allocations USING btree (supplier_payment_id);


--
-- Name: ix_supplier_payments_payment_reference; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_supplier_payments_payment_reference ON public.supplier_payments USING btree (payment_reference);


--
-- Name: ix_supplier_payments_supplier_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_supplier_payments_supplier_id ON public.supplier_payments USING btree (supplier_id);


--
-- Name: ix_suppliers_company_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_suppliers_company_name ON public.suppliers USING btree (company_name);


--
-- Name: ix_suppliers_supplier_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_suppliers_supplier_code ON public.suppliers USING btree (supplier_code);


--
-- Name: ix_survey_approvals_reviewer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_survey_approvals_reviewer_id ON public.survey_approvals USING btree (reviewer_id);


--
-- Name: ix_survey_approvals_survey_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_survey_approvals_survey_id ON public.survey_approvals USING btree (survey_id);


--
-- Name: ix_surveys_enquiry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_surveys_enquiry_id ON public.surveys USING btree (enquiry_id);


--
-- Name: ix_surveys_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_surveys_status ON public.surveys USING btree (status);


--
-- Name: ix_surveys_survey_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_surveys_survey_number ON public.surveys USING btree (survey_number);


--
-- Name: ix_surveys_surveyor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_surveys_surveyor_id ON public.surveys USING btree (surveyor_id);


--
-- Name: ix_task_assignments_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_assignments_employee_id ON public.task_assignments USING btree (employee_id);


--
-- Name: ix_task_assignments_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_assignments_task_id ON public.task_assignments USING btree (task_id);


--
-- Name: ix_task_history_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_history_task_id ON public.task_history USING btree (task_id);


--
-- Name: ix_tasks_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tasks_project_id ON public.tasks USING btree (project_id);


--
-- Name: ix_tasks_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tasks_status ON public.tasks USING btree (status);


--
-- Name: ix_tasks_task_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_tasks_task_code ON public.tasks USING btree (task_code);


--
-- Name: ix_tasks_task_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tasks_task_type ON public.tasks USING btree (task_type);


--
-- Name: ix_technician_payments_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_technician_payments_employee_id ON public.technician_payments USING btree (employee_id);


--
-- Name: ix_technician_payments_installation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_technician_payments_installation_id ON public.technician_payments USING btree (installation_id);


--
-- Name: ix_technician_payments_payment_reference; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_technician_payments_payment_reference ON public.technician_payments USING btree (payment_reference);


--
-- Name: ix_technician_worklogs_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_technician_worklogs_employee_id ON public.technician_worklogs USING btree (employee_id);


--
-- Name: ix_technician_worklogs_installation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_technician_worklogs_installation_id ON public.technician_worklogs USING btree (installation_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_phone ON public.users USING btree (phone);


--
-- Name: ix_users_role_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_role_id ON public.users USING btree (role_id);


--
-- Name: ix_warranty_events_warranty_record_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_events_warranty_record_id ON public.warranty_events USING btree (warranty_record_id);


--
-- Name: ix_warranty_policies_policy_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_warranty_policies_policy_code ON public.warranty_policies USING btree (policy_code);


--
-- Name: ix_warranty_policies_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_policies_product_id ON public.warranty_policies USING btree (product_id);


--
-- Name: ix_warranty_records_certificate_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_warranty_records_certificate_number ON public.warranty_records USING btree (certificate_number);


--
-- Name: ix_warranty_records_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_records_customer_id ON public.warranty_records USING btree (customer_id);


--
-- Name: ix_warranty_records_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_records_product_id ON public.warranty_records USING btree (product_id);


--
-- Name: ix_warranty_records_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_records_project_id ON public.warranty_records USING btree (project_id);


--
-- Name: ix_warranty_records_serial_number_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_records_serial_number_id ON public.warranty_records USING btree (serial_number_id);


--
-- Name: ix_warranty_records_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_records_status ON public.warranty_records USING btree (status);


--
-- Name: ix_warranty_records_warranty_policy_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_warranty_records_warranty_policy_id ON public.warranty_records USING btree (warranty_policy_id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: bom_items bom_items_bom_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_items
    ADD CONSTRAINT bom_items_bom_template_id_fkey FOREIGN KEY (bom_template_id) REFERENCES public.bom_templates(id) ON DELETE CASCADE;


--
-- Name: bom_items bom_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_items
    ADD CONSTRAINT bom_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: bom_templates bom_templates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bom_templates
    ADD CONSTRAINT bom_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: customer_acceptances customer_acceptances_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_acceptances
    ADD CONSTRAINT customer_acceptances_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: customer_acceptances customer_acceptances_customer_signature_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_acceptances
    ADD CONSTRAINT customer_acceptances_customer_signature_id_fkey FOREIGN KEY (customer_signature_id) REFERENCES public.file_attachments(id) ON DELETE SET NULL;


--
-- Name: customer_acceptances customer_acceptances_installation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_acceptances
    ADD CONSTRAINT customer_acceptances_installation_id_fkey FOREIGN KEY (installation_id) REFERENCES public.installations(id) ON DELETE RESTRICT;


--
-- Name: customer_acceptances customer_acceptances_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_acceptances
    ADD CONSTRAINT customer_acceptances_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: customers customers_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: customers customers_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: delivery_confirmations delivery_confirmations_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_confirmations
    ADD CONSTRAINT delivery_confirmations_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: delivery_confirmations delivery_confirmations_dispatch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_confirmations
    ADD CONSTRAINT delivery_confirmations_dispatch_id_fkey FOREIGN KEY (dispatch_id) REFERENCES public.dispatches(id) ON DELETE RESTRICT;


--
-- Name: delivery_confirmations delivery_confirmations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_confirmations
    ADD CONSTRAINT delivery_confirmations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: delivery_confirmations delivery_confirmations_signature_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.delivery_confirmations
    ADD CONSTRAINT delivery_confirmations_signature_attachment_id_fkey FOREIGN KEY (signature_attachment_id) REFERENCES public.file_attachments(id) ON DELETE SET NULL;


--
-- Name: departments departments_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: dispatch_items dispatch_items_dispatch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_items
    ADD CONSTRAINT dispatch_items_dispatch_id_fkey FOREIGN KEY (dispatch_id) REFERENCES public.dispatches(id) ON DELETE CASCADE;


--
-- Name: dispatch_items dispatch_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_items
    ADD CONSTRAINT dispatch_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: dispatch_serials dispatch_serials_dispatch_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_serials
    ADD CONSTRAINT dispatch_serials_dispatch_item_id_fkey FOREIGN KEY (dispatch_item_id) REFERENCES public.dispatch_items(id) ON DELETE CASCADE;


--
-- Name: dispatch_serials dispatch_serials_scanned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_serials
    ADD CONSTRAINT dispatch_serials_scanned_by_fkey FOREIGN KEY (scanned_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: dispatch_serials dispatch_serials_serial_number_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatch_serials
    ADD CONSTRAINT dispatch_serials_serial_number_id_fkey FOREIGN KEY (serial_number_id) REFERENCES public.serial_numbers(id) ON DELETE RESTRICT;


--
-- Name: dispatches dispatches_dispatched_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatches
    ADD CONSTRAINT dispatches_dispatched_by_fkey FOREIGN KEY (dispatched_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: dispatches dispatches_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatches
    ADD CONSTRAINT dispatches_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE RESTRICT;


--
-- Name: dispatches dispatches_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dispatches
    ADD CONSTRAINT dispatches_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: employee_certifications employee_certifications_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_certifications
    ADD CONSTRAINT employee_certifications_attachment_id_fkey FOREIGN KEY (attachment_id) REFERENCES public.file_attachments(id) ON DELETE SET NULL;


--
-- Name: employee_certifications employee_certifications_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_certifications
    ADD CONSTRAINT employee_certifications_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_skills employee_skills_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_skills employee_skills_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE RESTRICT;


--
-- Name: employee_skills employee_skills_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_skills
    ADD CONSTRAINT employee_skills_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: employees employees_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE RESTRICT;


--
-- Name: employees employees_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: enquiries enquiries_assigned_sales_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enquiries
    ADD CONSTRAINT enquiries_assigned_sales_id_fkey FOREIGN KEY (assigned_sales_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: enquiries enquiries_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enquiries
    ADD CONSTRAINT enquiries_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: escalations escalations_escalated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalations
    ADD CONSTRAINT escalations_escalated_by_fkey FOREIGN KEY (escalated_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: escalations escalations_escalated_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalations
    ADD CONSTRAINT escalations_escalated_to_fkey FOREIGN KEY (escalated_to) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: escalations escalations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalations
    ADD CONSTRAINT escalations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: escalations escalations_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.escalations
    ADD CONSTRAINT escalations_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: expenses expenses_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: expenses expenses_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE RESTRICT;


--
-- Name: expenses expenses_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: expenses expenses_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: expenses expenses_receipt_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_receipt_attachment_id_fkey FOREIGN KEY (receipt_attachment_id) REFERENCES public.file_attachments(id) ON DELETE SET NULL;


--
-- Name: file_attachments file_attachments_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_attachments
    ADD CONSTRAINT file_attachments_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: followups followups_conducted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.followups
    ADD CONSTRAINT followups_conducted_by_fkey FOREIGN KEY (conducted_by) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: followups followups_enquiry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.followups
    ADD CONSTRAINT followups_enquiry_id_fkey FOREIGN KEY (enquiry_id) REFERENCES public.enquiries(id) ON DELETE CASCADE;


--
-- Name: goods_receipt_items goods_receipt_items_goods_receipt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT goods_receipt_items_goods_receipt_id_fkey FOREIGN KEY (goods_receipt_id) REFERENCES public.goods_receipts(id) ON DELETE CASCADE;


--
-- Name: goods_receipt_items goods_receipt_items_po_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT goods_receipt_items_po_item_id_fkey FOREIGN KEY (po_item_id) REFERENCES public.purchase_order_items(id) ON DELETE RESTRICT;


--
-- Name: goods_receipt_items goods_receipt_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT goods_receipt_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: goods_receipts goods_receipts_purchase_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT goods_receipts_purchase_order_id_fkey FOREIGN KEY (purchase_order_id) REFERENCES public.purchase_orders(id) ON DELETE RESTRICT;


--
-- Name: goods_receipts goods_receipts_received_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT goods_receipts_received_by_fkey FOREIGN KEY (received_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: goods_receipts goods_receipts_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT goods_receipts_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE RESTRICT;


--
-- Name: installation_checklists installation_checklists_installation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_checklists
    ADD CONSTRAINT installation_checklists_installation_id_fkey FOREIGN KEY (installation_id) REFERENCES public.installations(id) ON DELETE CASCADE;


--
-- Name: installation_checklists installation_checklists_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_checklists
    ADD CONSTRAINT installation_checklists_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: installation_photos installation_photos_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_photos
    ADD CONSTRAINT installation_photos_attachment_id_fkey FOREIGN KEY (attachment_id) REFERENCES public.file_attachments(id) ON DELETE RESTRICT;


--
-- Name: installation_photos installation_photos_installation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_photos
    ADD CONSTRAINT installation_photos_installation_id_fkey FOREIGN KEY (installation_id) REFERENCES public.installations(id) ON DELETE CASCADE;


--
-- Name: installation_schedule_technicians installation_schedule_technicians_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedule_technicians
    ADD CONSTRAINT installation_schedule_technicians_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: installation_schedule_technicians installation_schedule_technicians_schedule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedule_technicians
    ADD CONSTRAINT installation_schedule_technicians_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES public.installation_schedules(id) ON DELETE CASCADE;


--
-- Name: installation_schedules installation_schedules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedules
    ADD CONSTRAINT installation_schedules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: installation_schedules installation_schedules_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_schedules
    ADD CONSTRAINT installation_schedules_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: installation_tests installation_tests_installation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_tests
    ADD CONSTRAINT installation_tests_installation_id_fkey FOREIGN KEY (installation_id) REFERENCES public.installations(id) ON DELETE CASCADE;


--
-- Name: installation_tests installation_tests_tested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installation_tests
    ADD CONSTRAINT installation_tests_tested_by_fkey FOREIGN KEY (tested_by) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: installations installations_lead_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installations
    ADD CONSTRAINT installations_lead_technician_id_fkey FOREIGN KEY (lead_technician_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: installations installations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installations
    ADD CONSTRAINT installations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: installations installations_schedule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.installations
    ADD CONSTRAINT installations_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES public.installation_schedules(id) ON DELETE SET NULL;


--
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: invoice_items invoice_items_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice_items
    ADD CONSTRAINT invoice_items_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id) ON DELETE CASCADE;


--
-- Name: invoice_items invoice_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice_items
    ADD CONSTRAINT invoice_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: invoices invoices_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: invoices invoices_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE RESTRICT;


--
-- Name: invoices invoices_pdf_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pdf_attachment_id_fkey FOREIGN KEY (pdf_attachment_id) REFERENCES public.file_attachments(id) ON DELETE SET NULL;


--
-- Name: invoices invoices_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: material_consumption material_consumption_installation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_consumption
    ADD CONSTRAINT material_consumption_installation_id_fkey FOREIGN KEY (installation_id) REFERENCES public.installations(id) ON DELETE CASCADE;


--
-- Name: material_consumption material_consumption_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_consumption
    ADD CONSTRAINT material_consumption_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: material_consumption material_consumption_serial_number_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_consumption
    ADD CONSTRAINT material_consumption_serial_number_id_fkey FOREIGN KEY (serial_number_id) REFERENCES public.serial_numbers(id) ON DELETE SET NULL;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: orders orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: orders orders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: orders orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id) ON DELETE RESTRICT;


--
-- Name: payment_allocations payment_allocations_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_allocations
    ADD CONSTRAINT payment_allocations_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id) ON DELETE RESTRICT;


--
-- Name: payment_allocations payment_allocations_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_allocations
    ADD CONSTRAINT payment_allocations_payment_id_fkey FOREIGN KEY (payment_id) REFERENCES public.payments(id) ON DELETE RESTRICT;


--
-- Name: payments payments_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: payments payments_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE RESTRICT;


--
-- Name: payments payments_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: payments payments_received_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_received_by_fkey FOREIGN KEY (received_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: project_bom_items project_bom_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_bom_items
    ADD CONSTRAINT project_bom_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: project_bom_items project_bom_items_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_bom_items
    ADD CONSTRAINT project_bom_items_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_costs project_costs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_costs
    ADD CONSTRAINT project_costs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_costs project_costs_recorded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_costs
    ADD CONSTRAINT project_costs_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: project_notes project_notes_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_notes
    ADD CONSTRAINT project_notes_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: project_notes project_notes_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_notes
    ADD CONSTRAINT project_notes_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: projects projects_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: projects projects_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE RESTRICT;


--
-- Name: projects projects_project_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_project_manager_id_fkey FOREIGN KEY (project_manager_id) REFERENCES public.employees(id) ON DELETE SET NULL;


--
-- Name: purchase_order_items purchase_order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT purchase_order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: purchase_order_items purchase_order_items_purchase_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT purchase_order_items_purchase_order_id_fkey FOREIGN KEY (purchase_order_id) REFERENCES public.purchase_orders(id) ON DELETE CASCADE;


--
-- Name: purchase_orders purchase_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: purchase_orders purchase_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: purchase_orders purchase_orders_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE RESTRICT;


--
-- Name: quotation_items quotation_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_items
    ADD CONSTRAINT quotation_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: quotation_items quotation_items_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_items
    ADD CONSTRAINT quotation_items_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id) ON DELETE CASCADE;


--
-- Name: quotation_revisions quotation_revisions_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_revisions
    ADD CONSTRAINT quotation_revisions_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id) ON DELETE CASCADE;


--
-- Name: quotation_revisions quotation_revisions_revised_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_revisions
    ADD CONSTRAINT quotation_revisions_revised_by_fkey FOREIGN KEY (revised_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: quotations quotations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: quotations quotations_enquiry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_enquiry_id_fkey FOREIGN KEY (enquiry_id) REFERENCES public.enquiries(id) ON DELETE RESTRICT;


--
-- Name: quotations quotations_survey_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_survey_id_fkey FOREIGN KEY (survey_id) REFERENCES public.surveys(id) ON DELETE SET NULL;


--
-- Name: replacements replacements_original_serial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replacements
    ADD CONSTRAINT replacements_original_serial_id_fkey FOREIGN KEY (original_serial_id) REFERENCES public.serial_numbers(id) ON DELETE RESTRICT;


--
-- Name: replacements replacements_replaced_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replacements
    ADD CONSTRAINT replacements_replaced_by_fkey FOREIGN KEY (replaced_by) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: replacements replacements_replacement_serial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replacements
    ADD CONSTRAINT replacements_replacement_serial_id_fkey FOREIGN KEY (replacement_serial_id) REFERENCES public.serial_numbers(id) ON DELETE RESTRICT;


--
-- Name: replacements replacements_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replacements
    ADD CONSTRAINT replacements_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.service_tickets(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: serial_number_history serial_number_history_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_number_history
    ADD CONSTRAINT serial_number_history_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: serial_number_history serial_number_history_recorded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_number_history
    ADD CONSTRAINT serial_number_history_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: serial_number_history serial_number_history_serial_number_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_number_history
    ADD CONSTRAINT serial_number_history_serial_number_id_fkey FOREIGN KEY (serial_number_id) REFERENCES public.serial_numbers(id) ON DELETE CASCADE;


--
-- Name: serial_numbers serial_numbers_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_numbers
    ADD CONSTRAINT serial_numbers_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id) ON DELETE SET NULL;


--
-- Name: serial_numbers serial_numbers_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_numbers
    ADD CONSTRAINT serial_numbers_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: serial_numbers serial_numbers_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_numbers
    ADD CONSTRAINT serial_numbers_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: serial_numbers serial_numbers_purchase_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_numbers
    ADD CONSTRAINT serial_numbers_purchase_order_id_fkey FOREIGN KEY (purchase_order_id) REFERENCES public.purchase_orders(id) ON DELETE SET NULL;


--
-- Name: serial_numbers serial_numbers_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.serial_numbers
    ADD CONSTRAINT serial_numbers_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE SET NULL;


--
-- Name: service_ticket_confirmations service_ticket_confirmations_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_ticket_confirmations
    ADD CONSTRAINT service_ticket_confirmations_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: service_ticket_confirmations service_ticket_confirmations_signature_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_ticket_confirmations
    ADD CONSTRAINT service_ticket_confirmations_signature_attachment_id_fkey FOREIGN KEY (signature_attachment_id) REFERENCES public.file_attachments(id) ON DELETE SET NULL;


--
-- Name: service_ticket_confirmations service_ticket_confirmations_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_ticket_confirmations
    ADD CONSTRAINT service_ticket_confirmations_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.service_tickets(id) ON DELETE RESTRICT;


--
-- Name: service_tickets service_tickets_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_tickets
    ADD CONSTRAINT service_tickets_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: service_tickets service_tickets_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_tickets
    ADD CONSTRAINT service_tickets_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: service_tickets service_tickets_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_tickets
    ADD CONSTRAINT service_tickets_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: service_tickets service_tickets_serial_number_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_tickets
    ADD CONSTRAINT service_tickets_serial_number_id_fkey FOREIGN KEY (serial_number_id) REFERENCES public.serial_numbers(id) ON DELETE SET NULL;


--
-- Name: service_tickets service_tickets_warranty_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_tickets
    ADD CONSTRAINT service_tickets_warranty_record_id_fkey FOREIGN KEY (warranty_record_id) REFERENCES public.warranty_records(id) ON DELETE SET NULL;


--
-- Name: service_visits service_visits_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_visits
    ADD CONSTRAINT service_visits_technician_id_fkey FOREIGN KEY (technician_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: service_visits service_visits_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_visits
    ADD CONSTRAINT service_visits_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.service_tickets(id) ON DELETE CASCADE;


--
-- Name: stock_movements stock_movements_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id) ON DELETE RESTRICT;


--
-- Name: stock_movements stock_movements_performed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_performed_by_fkey FOREIGN KEY (performed_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: stock_movements stock_movements_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: stock_reservations stock_reservations_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_reservations
    ADD CONSTRAINT stock_reservations_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id) ON DELETE RESTRICT;


--
-- Name: stock_reservations stock_reservations_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_reservations
    ADD CONSTRAINT stock_reservations_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: stock_reservations stock_reservations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_reservations
    ADD CONSTRAINT stock_reservations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: stock_reservations stock_reservations_reserved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stock_reservations
    ADD CONSTRAINT stock_reservations_reserved_by_fkey FOREIGN KEY (reserved_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: subsidy_applications subsidy_applications_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_applications
    ADD CONSTRAINT subsidy_applications_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: subsidy_applications subsidy_applications_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_applications
    ADD CONSTRAINT subsidy_applications_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: subsidy_applications subsidy_applications_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_applications
    ADD CONSTRAINT subsidy_applications_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: subsidy_documents subsidy_documents_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_documents
    ADD CONSTRAINT subsidy_documents_attachment_id_fkey FOREIGN KEY (attachment_id) REFERENCES public.file_attachments(id) ON DELETE RESTRICT;


--
-- Name: subsidy_documents subsidy_documents_subsidy_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_documents
    ADD CONSTRAINT subsidy_documents_subsidy_application_id_fkey FOREIGN KEY (subsidy_application_id) REFERENCES public.subsidy_applications(id) ON DELETE CASCADE;


--
-- Name: subsidy_documents subsidy_documents_verified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_documents
    ADD CONSTRAINT subsidy_documents_verified_by_fkey FOREIGN KEY (verified_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: subsidy_payments subsidy_payments_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_payments
    ADD CONSTRAINT subsidy_payments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: subsidy_payments subsidy_payments_subsidy_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_payments
    ADD CONSTRAINT subsidy_payments_subsidy_application_id_fkey FOREIGN KEY (subsidy_application_id) REFERENCES public.subsidy_applications(id) ON DELETE RESTRICT;


--
-- Name: subsidy_status_history subsidy_status_history_subsidy_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_status_history
    ADD CONSTRAINT subsidy_status_history_subsidy_application_id_fkey FOREIGN KEY (subsidy_application_id) REFERENCES public.subsidy_applications(id) ON DELETE CASCADE;


--
-- Name: subsidy_status_history subsidy_status_history_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subsidy_status_history
    ADD CONSTRAINT subsidy_status_history_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: supplier_invoices supplier_invoices_attachment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT supplier_invoices_attachment_id_fkey FOREIGN KEY (attachment_id) REFERENCES public.file_attachments(id) ON DELETE SET NULL;


--
-- Name: supplier_invoices supplier_invoices_purchase_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT supplier_invoices_purchase_order_id_fkey FOREIGN KEY (purchase_order_id) REFERENCES public.purchase_orders(id) ON DELETE RESTRICT;


--
-- Name: supplier_invoices supplier_invoices_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT supplier_invoices_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE RESTRICT;


--
-- Name: supplier_payment_allocations supplier_payment_allocations_supplier_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payment_allocations
    ADD CONSTRAINT supplier_payment_allocations_supplier_invoice_id_fkey FOREIGN KEY (supplier_invoice_id) REFERENCES public.supplier_invoices(id) ON DELETE RESTRICT;


--
-- Name: supplier_payment_allocations supplier_payment_allocations_supplier_payment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payment_allocations
    ADD CONSTRAINT supplier_payment_allocations_supplier_payment_id_fkey FOREIGN KEY (supplier_payment_id) REFERENCES public.supplier_payments(id) ON DELETE RESTRICT;


--
-- Name: supplier_payments supplier_payments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payments
    ADD CONSTRAINT supplier_payments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: supplier_payments supplier_payments_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.supplier_payments
    ADD CONSTRAINT supplier_payments_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE RESTRICT;


--
-- Name: survey_approvals survey_approvals_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_approvals
    ADD CONSTRAINT survey_approvals_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: survey_approvals survey_approvals_survey_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_approvals
    ADD CONSTRAINT survey_approvals_survey_id_fkey FOREIGN KEY (survey_id) REFERENCES public.surveys(id) ON DELETE CASCADE;


--
-- Name: surveys surveys_enquiry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surveys
    ADD CONSTRAINT surveys_enquiry_id_fkey FOREIGN KEY (enquiry_id) REFERENCES public.enquiries(id) ON DELETE RESTRICT;


--
-- Name: surveys surveys_surveyor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surveys
    ADD CONSTRAINT surveys_surveyor_id_fkey FOREIGN KEY (surveyor_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: task_assignments task_assignments_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_assignments
    ADD CONSTRAINT task_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: task_assignments task_assignments_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_assignments
    ADD CONSTRAINT task_assignments_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: task_assignments task_assignments_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_assignments
    ADD CONSTRAINT task_assignments_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: task_history task_history_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_history
    ADD CONSTRAINT task_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: task_history task_history_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_history
    ADD CONSTRAINT task_history_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: tasks tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: technician_payments technician_payments_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_payments
    ADD CONSTRAINT technician_payments_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: technician_payments technician_payments_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_payments
    ADD CONSTRAINT technician_payments_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: technician_payments technician_payments_installation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_payments
    ADD CONSTRAINT technician_payments_installation_id_fkey FOREIGN KEY (installation_id) REFERENCES public.installations(id) ON DELETE SET NULL;


--
-- Name: technician_worklogs technician_worklogs_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_worklogs
    ADD CONSTRAINT technician_worklogs_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: technician_worklogs technician_worklogs_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_worklogs
    ADD CONSTRAINT technician_worklogs_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE RESTRICT;


--
-- Name: technician_worklogs technician_worklogs_installation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.technician_worklogs
    ADD CONSTRAINT technician_worklogs_installation_id_fkey FOREIGN KEY (installation_id) REFERENCES public.installations(id) ON DELETE CASCADE;


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE RESTRICT;


--
-- Name: warranty_events warranty_events_recorded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_events
    ADD CONSTRAINT warranty_events_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: warranty_events warranty_events_warranty_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_events
    ADD CONSTRAINT warranty_events_warranty_record_id_fkey FOREIGN KEY (warranty_record_id) REFERENCES public.warranty_records(id) ON DELETE CASCADE;


--
-- Name: warranty_policies warranty_policies_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_policies
    ADD CONSTRAINT warranty_policies_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: warranty_records warranty_records_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_records
    ADD CONSTRAINT warranty_records_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE RESTRICT;


--
-- Name: warranty_records warranty_records_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_records
    ADD CONSTRAINT warranty_records_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE RESTRICT;


--
-- Name: warranty_records warranty_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_records
    ADD CONSTRAINT warranty_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE RESTRICT;


--
-- Name: warranty_records warranty_records_serial_number_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_records
    ADD CONSTRAINT warranty_records_serial_number_id_fkey FOREIGN KEY (serial_number_id) REFERENCES public.serial_numbers(id) ON DELETE RESTRICT;


--
-- Name: warranty_records warranty_records_warranty_policy_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warranty_records
    ADD CONSTRAINT warranty_records_warranty_policy_id_fkey FOREIGN KEY (warranty_policy_id) REFERENCES public.warranty_policies(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict h9ZPbolvCueoa1iwds2aqbXojlgmr4NJ2jbw26QdABu0fAcb47crxJVskShZVQE

