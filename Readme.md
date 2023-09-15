# API DESIGN

### Konseling

1. Create
   Header :

```
   {
    Token, Content(Application/json)
    Params : -
   }
```

Input(Body) :

```json
    {
      "student_code":,
      "scope_code":,
      "category_code":,
      "employee_code"	:,
      "counselling_date":,
      "problem":,
      "conclusion":,
      "followup":,
      "counselling_note":,
    }
```

Output(Response) :
Jika success

```json
{
  "success": true
}
```

Jika success

```json
    {
		  "success": false,
      "message": error
    }
```

2. Edit 3. Delete 4. Paging 5. Select One(?)

## TESTCASE API

### SCOPE API

1. CREATE AND EDIT SCOPE API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "scope_name": "Scope baru test",
  "scope_note": "Scope yang ada notesnya"
}
```

B. TESTCASE KEDUA

```json
{
  "scope_name": "Scope baru test"
}
```

CASE GAGAL:

TESTCASE PERTAMA

```json
{
  "scope_note": "Scope yang ada notesnya"
}
```

TESTCASE KEDUA

```json
{}
```

2. Filter API

```json
{
  "filter_type": "AND",
  "filters": [
    {
      "search": "scope_name",
      "value": "S"
    },
    {
      "search": "scope_code",
      "value": "0002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

### CATEGORY API

1. CREATE AND EDIT CATEGORY API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "category_name": "Category baru test",
  "category_note": "Category yang ada notesnya"
}
```

B. TESTCASE KEDUA

```json
{
  "category_name": "Category baru test"
}
```

CASE GAGAL:

TESTCASE PERTAMA

```json
{
  "category_note": "Category yang ada notesnya"
}
```

TESTCASE KEDUA

```json
{}
```

2. Filter API

```json
{
  "filter_type": "AND",
  "filters": [
    {
      "search": "category_name",
      "value": "S"
    },
    {
      "search": "category_code",
      "value": "0002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

### UNIVERSITY API

1. CREATE AND EDIT UNIVERSITY API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "university_name": "University baru test",
  "university_note": "University yang ada notesnya"
}
```

B. TESTCASE KEDUA

```json
{
  "university_name": "University baru test"
}
```

CASE GAGAL:

TESTCASE PERTAMA

```json
{
  "university_note": "University yang ada notesnya"
}
```

TESTCASE KEDUA

```json
{}
```

2. Filter API

```json
{
  "filter_type": "AND",
  "filters": [
    {
      "search": "university_name",
      "value": "S"
    },
    {
      "search": "university_code",
      "value": "0002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

### FACULTY API

1. CREATE AND EDIT FACULTY API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "faculty_name": "Faculty baru test",
  "university_code": "UNV23090002",
  "faculty_note": "Faculty yang ada notesnya"
}
```

B. TESTCASE KEDUA

```json
{
  "faculty_name": "Faculty baru test",
  "university_code": "UNV23090002"
}
```

CASE GAGAL:

TESTCASE PERTAMA

```json
{
  "faculty_note": "Faculty yang ada notesnya"
}
```

TESTCASE KEDUA

```json
{
  "faculty_name": "Faculty baru test"
}
```

2. Filter API

CASE PERTAMA

```json
{
  "filter_type": "AND",
  "filters": [
    {
      "search": "faculty_name",
      "value": "S"
    },
    {
      "search": "faculty_code",
      "value": "0002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

CASE KEDUA

```json
{
  "filter_type": "OR",
  "filters": [
    {
      "search": "university_code",
      "value": "UNV23090002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

### FACULTY API

1. CREATE AND EDIT FACULTY API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "study_program_name": "Teknik Informatika",
  "faculty_code": "FAL23090002",
  "study_program_note": "Teknik Informatika"
}
```

B. TESTCASE KEDUA

```json
{
  "study_program_name": "Matematika Murni",
  "faculty_code": "FAL23090003"
}
```

```json
{
  "study_program_name": "Fisika",
  "faculty_code": "FAL23090003"
}
```

CASE GAGAL:

TESTCASE PERTAMA

```json
{
  "study_program_note": "Faculty yang ada notesnya"
}
```

TESTCASE KEDUA

```json
{
  "study_program_name": "Faculty baru test"
}
```

2. Filter API

CASE PERTAMA

```json
{
  "filter_type": "AND",
  "filters": [
    {
      "search": "study_program_name",
      "value": "S"
    },
    {
      "search": "study_program_code",
      "value": "0002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

CASE KEDUA

```json
{
  "filter_type": "OR",
  "filters": [
    {
      "search": "faculty_code",
      "value": "UNV23090002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

### PROVIDER API

1. CREATE AND EDIT PROVIDER API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "provider_name": "Dr. ABC",
  "phone": "72465275",
  "provider_note": "asssss"
}
```

B. TESTCASE KEDUA

```json
{
  "provider_name": "Dr. DEF",
  "phone": "7214643"
}
```

CASE GAGAL:

TESTCASE PERTAMA

```json
{
  "provider_note": "Provider yang ada notesnya"
}
```

TESTCASE KEDUA

```json
{
  "provider_name": "Provider baru test"
}
```

2. Filter API

CASE PERTAMA

```json
{
  "filter_type": "AND",
  "filters": [
    {
      "search": "provider_name",
      "value": "S"
    },
    {
      "search": "provider_code",
      "value": "0002"
    }
  ],
  "limit": 10,
  "page": 1
}
```

### COUNSELING API

1. CREATE AND EDIT COUNSELING API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "student_code": "7283657",
  "scope_code": "SC23090003",
  "category_code": "C23090002",
  "employee_code": "155275",
  "counseling_date": "2023/09/15",
  "problem": "Problem A",
  "conclusion": "Conclusion A",
  "followup": "Follow Up A",
  "counseling_note": ""
}
```

CASE GAGAL:

```json
{
  "student_code": "7283657",
  "scope_code": "SC23090003",
  "category_code": "C23090002",
  "employee_code": "155275",
  "problem": "Problem A",
  "conclusion": "Conclusion A",
  "followup": "Follow Up A",
  "counseling_note": ""
}
```

### CONSULTATION API

1. CREATE AND EDIT CONSULTATION API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "student_code": "542852856",
  "scope_code": "SC23090003",
  "employee_code": "421626",
  "consultation_date": "2023/09/15",
  "problem": "Problem B",
  "conclusion": "Conclusion B",
  "followup": "Follow Up B",
  "consultation_note": ""
}
```

CASE GAGAL:

```json
{
  "student_code": "7283657",
  "scope_code": "SC23090003",
  "category_code": "C23090002",
  "employee_code": "155275",
  "problem": "Problem A",
  "conclusion": "Conclusion A",
  "followup": "Follow Up A",
  "consultation_note": ""
}
```

### VISIT API

1. CREATE AND EDIT VISIT API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "student_code": "542852856",
  "employee_code": "421626",
  "visit_date": "2023/09/15",
  "reason": "Problem B",
  "result": "Conclusion B",
  "followup": "Follow Up B",
  "visit_note": ""
}
```

CASE GAGAL:

```json
{
  "student_code": "7283657",
  "scope_code": "SC23090003",
  "category_code": "C23090002",
  "employee_code": "155275",
  "problem": "Problem A",
  "conclusion": "Conclusion A",
  "followup": "Follow Up A",
  "visit_note": ""
}
```

### CASE TRANSFER API

1. CREATE AND EDIT CASE TRANSFER API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "student_code": "542852856",
  "provider_code": "P23090002",
  "employee_code": "421626",
  "case_transfer_date": "2023/09/15",
  "result": "Conclusion B",
  "followup": "Follow Up B",
  "case_transfer_note": ""
}
```

CASE GAGAL:

```json
{
  "student_code": "7283657",
  "scope_code": "SC23090003",
  "category_code": "C23090002",
  "employee_code": "155275",
  "problem": "Problem A",
  "conclusion": "Conclusion A",
  "followup": "Follow Up A",
  "case_transfer_note": ""
}
```

### CASE TRANSFER API

1. CREATE AND EDIT CASE TRANSFER API

CASE BERHASIL:

A. TESCASE PERTAMA

```json
{
  "student_code": "542852856",
  "study_program_code": "P23090002",
  "employee_code": "421626",
  "continuing_study_date": "2023/09/15",
  "result": "Conclusion B",
  "followup": "Follow Up B",
  "continuing_study_note": ""
}
```

CASE GAGAL:

```json
{
  "student_code": "7283657",
  "study_program_code": "SC23090003",
  "category_code": "C23090002",
  "employee_code": "155275",
  "problem": "Problem A",
  "conclusion": "Conclusion A",
  "followup": "Follow Up A",
  "study_program_note": ""
}
```
