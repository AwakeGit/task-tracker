# ERD

## Сущности

**users**
- id (PK)
- email (UNIQUE)
- name
- hashed_password

**tasks**
- id (PK)
- title
- description
- theme
- status: ENUM(new, in_progress, done, cancelled), по умолчанию new
- owner_id (FK → users.id) — кто создал задачу
- executor_id (FK → users.id, NULL) — кто исполняет
- created_at, updated_at

## Связи

- users 1—N tasks (owner): один пользователь создаёт много задач.
- users 1—N tasks (executor): один пользователь исполняет много задач (необязательная связь).

## Диаграмма

```
+-------------+                 +-------------------+
|    users    |                 |       tasks       |
+-------------+                 +-------------------+
| id (PK)     | 1             N | id (PK)           |
| email (UQ)  |----------------<| title             |
| name        |  owner_id (FK)  | description       |
| hashed_pass |                 | theme             |
+-------------+                 | status            |
              | 1             N | owner_id (FK)     |
              |----------------<| executor_id (FK)  |
               executor_id (FK) | created_at        |
                                | updated_at        |
                                +-------------------+
```
