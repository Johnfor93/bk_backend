CREATE TABLE b_route(
    route_name varchar,
    route_method varchar,
    PRIMARY KEY(route_name, route_method)
);

CREATE TABLE m_user_route(
    user_code varchar(40),
    route_name varchar(40),
    route_method varchar(40),
    user_route_note text,
    is_active char(1),
    create_by varchar(40),
    create_date timestamptz,
    update_by varchar(40),
    update_date timestamptz,

    CONSTRAINT fk_user_route FOREIGN KEY(route_name, route_method) REFERENCES b_route(route_name, route_method)
);

CREATE TABLE l_user_response(
    user_code varchar(40),
    route_name varchar(40),
    route_method varchar(40),
    request_time timestamptz(6) not null,
    response_code varchar(40) not null,
    response_message text not null,

    CONSTRAINT fk_user_respons FOREIGN KEY(route_name, route_method) REFERENCES b_route(route_name, route_method)
);

CREATE TABLE m_university  (
  university_code varchar(40) NOT NULL,
  university_name varchar(100) NOT NULL,
  university_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (university_code)
);

CREATE TABLE m_faculty  (
  faculty_code varchar(40) NOT NULL,
  university_code varchar(40) NOT NULL,
  faculty_name varchar(100) NOT NULL,
  faculty_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (faculty_code),
  CONSTRAINT m_faculty_ibfk_1 FOREIGN KEY (university_code) REFERENCES m_university (university_code) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE m_study_program  (
  study_program_code varchar(40) NOT NULL,
  faculty_code varchar(40) NOT NULL,
  study_program_name varchar(100) NOT NULL,
  study_program_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz(0) NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz(0) NOT NULL,
  PRIMARY KEY (study_program_code),
  CONSTRAINT m_study_program_ibfk_1 FOREIGN KEY (faculty_code) REFERENCES m_faculty (faculty_code) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE m_category  (
  category_code varchar(40),
  category_name varchar(40),
  category_note text,
	is_active char(1),
  create_by varchar(40),
  create_date timestamptz NOT NULL,
  update_by varchar(40),
  update_date timestamptz NOT NULL,
  PRIMARY KEY (category_code)
);

CREATE TABLE m_provider  (
  provider_code varchar(40) NOT NULL,
  provider_name varchar(100) NOT NULL,
  phone varchar(40) NOT NULL,
  provider_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (provider_code)
);

CREATE TABLE m_scope  (
  scope_code varchar(40) NOT NULL,
  scope_name varchar(40) NOT NULL,
  scope_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (scope_code)
);

CREATE TABLE t_case_transfer  (
  case_transfer_code varchar(40) NOT NULL,
  student_code varchar(40) NOT NULL,
  provider_code varchar(40) NOT NULL,
  employee_code varchar(40) NOT NULL,
  case_transfer_date date NOT NULL,
  result text NOT NULL,
  followup text NOT NULL,
  case_transfer_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (case_transfer_code),
  CONSTRAINT t_case_transfer_ibfk_2 FOREIGN KEY (provider_code) REFERENCES m_provider (provider_code) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE t_consultation  (
  consultation_code varchar(40) NOT NULL,
  student_code varchar(40) NOT NULL,
  scope_code varchar(40) NOT NULL,
  employee_code varchar(40) NOT NULL,
  consultation_date date NOT NULL,
  problem text NOT NULL,
  conclusion text NOT NULL,
  followup text NOT NULL,
  consultation_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (consultation_code),
  CONSTRAINT t_consultation_ibfk_2 FOREIGN KEY (scope_code) REFERENCES m_scope (scope_code) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE t_continuing_study  (
  continuing_study_code varchar(40) NOT NULL,
  student_code varchar(40) NOT NULL,
  study_program_code varchar(40) NULL DEFAULT NULL,
  employee_code varchar(40) NOT NULL,
  continuing_study_date date NOT NULL,
  result text NOT NULL,
  continuing_study_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (continuing_study_code),
  CONSTRAINT t_continuing_study_ibfk_2 FOREIGN KEY (study_program_code) REFERENCES m_study_program (study_program_code) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE t_counseling  (
  counseling_code varchar(40)  NOT NULL,
  student_code varchar(40)  NOT NULL,
  scope_code varchar(40)  NOT NULL,
  category_code varchar(40)  NOT NULL,
  employee_code varchar(40)  NOT NULL,
  counseling_date date NOT NULL,
  problem text  NOT NULL,
  conclusion text  NOT NULL,
  followup text  NOT NULL,
  counseling_note text  NULL,
  is_active char(1)  NOT NULL,
  create_by varchar(40)  NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40)  NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (counseling_code),
  CONSTRAINT t_counseling_ibfk_2 FOREIGN KEY (scope_code) REFERENCES m_scope (scope_code) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT t_counseling_ibfk_3 FOREIGN KEY (category_code) REFERENCES m_category (category_code) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE t_visit  (
  visit_code varchar(40) NOT NULL,
  student_code varchar(40) NOT NULL,
  employee_code varchar(40) NOT NULL,
  visit_date date NOT NULL,
  reason text NOT NULL,
  result text NOT NULL,
  followup text NOT NULL,
  visit_note text NULL,
  is_active char(1) NOT NULL,
  create_by varchar(40) NOT NULL,
  create_date timestamptz NOT NULL,
  update_by varchar(40) NOT NULL,
  update_date timestamptz NOT NULL,
  PRIMARY KEY (visit_code)
);