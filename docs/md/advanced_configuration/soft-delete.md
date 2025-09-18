[← Back to Advanced Configuration index](index.md)

# Soft delete
`flarchitect` can mark records as deleted without removing them from the
database. This allows you to hide data from normal queries while retaining it
for auditing or future restoration.

## Configuration
Enable soft deletes and define how records are flagged:
```
class Config:
    API_SOFT_DELETE = True
    API_SOFT_DELETE_ATTRIBUTE = "deleted"
    API_SOFT_DELETE_VALUES = (False, True)
```
API_SOFT_DELETE_ATTRIBUTE <configuration.html#SOFT_DELETE_ATTRIBUTE> names the column that stores the deleted flag.
API_SOFT_DELETE_VALUES <configuration.html#SOFT_DELETE_VALUES> is a tuple where the first value represents an
active record and the second marks it as deleted.

## Example model
Add a boolean column to your base model so every table can inherit the flag:
```
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class BaseModel(DeclarativeBase):
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

db = SQLAlchemy(model_class=BaseModel)

class Book(db.Model):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
```

## Example queries
Soft deleted rows are hidden from normal requests:
```
GET /api/books        # returns rows where deleted=False
```
Include the `include_deleted` query parameter to return all rows:
```
GET /api/books?include_deleted=true
```
Issuing a DELETE request marks the record as deleted. To remove it
permanently, supply `cascade_delete=1`:
```
DELETE /api/books/1             # sets deleted=True
DELETE /api/books/1?cascade_delete=1  # removes row from database
```

