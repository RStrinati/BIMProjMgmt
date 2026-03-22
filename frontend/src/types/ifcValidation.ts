export type IfcIdsTest = {
  ids_test_id: number;
  project_id: number;
  ids_name: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type IfcValidationRun = {
  validation_run_id: number;
  project_id: number;
  expected_model_id: number | null;
  ids_test_id: number | null;
  ifc_filename: string;
  ids_filename: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  total_specifications: number | null;
  passed_specifications: number | null;
  failed_specifications: number | null;
  total_failures: number | null;
  created_at: string | null;
  updated_at: string | null;
};

export type IfcValidationFailure = {
  failure_id: number;
  specification_name: string;
  message: string | null;
  ifc_class: string | null;
  object_name: string | null;
  created_at: string | null;
};

export type IfcValidationSpecification = {
  name: string;
  description?: string;
  status: 'pass' | 'fail' | 'warn';
  fail_count: number;
  passed_count: number;
  failed_entities: Array<{
    message?: string;
    ifc_class?: string;
    object_name?: string;
  }>;
};

export type IfcValidationResult = {
  success: boolean;
  ifc_filename: string;
  ids_filename: string;
  summary: {
    total_specifications: number;
    passed_specifications: number;
    failed_specifications: number;
    total_entities_checked: number | null;
    total_failures: number;
  };
  specifications: IfcValidationSpecification[];
  errors: string[];
};
