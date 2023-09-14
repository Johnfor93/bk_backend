# API DESIGN

### Konseling

1. Create
   Header :

```json
   {
    Token, Content(Application/json)
    Params : -
   }
```

Input(Body) :

```json
    {
		Student_code:,
		Scope_code:,
		Category_code:,
        Employee_code	:,
        Counselling_date:,
        Problem:,
        Conclusion:,
        Followup:,
        Counselling_note:,
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
		success: false,
        message: error
    }
```

2. Edit 3. Delete 4. Paging 5. Select One(?)

## TESTCASE API

### SCOPE API

1. CREATE AND EDIT SCOPE API

CASE BERHASIL:

A. TESCASE PERTAMA

```
{
    "scope_name": "Scope baru test",
    "scope_note": "Scope yang ada notesnya"
}
```

B. TESTCASE KEDUA

```
{
    "scope_name": "Scope baru test"
}
```

CASE GAGAL:

TESTCASE PERTAMA

```
{
    "scope_note": "Scope yang ada notesnya"
}
```

TESTCASE KEDUA

```
{
}
```

2. Filter API

```
{
    "filter_type" : "AND",
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
