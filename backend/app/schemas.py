from marshmallow import Schema, fields, validate

class SignupSchema(Schema):
    password = fields.Str(required=True, validate=validate.Length(min=8))
    token = fields.Str(required=True)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class EmployeeSchema(Schema):
    email = fields.Email(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1))
    last_name = fields.Str(required=True, validate=validate.Length(min=1))
    position = fields.Str(required=True)
    department = fields.Str(required=True)
    phone = fields.Str(required=True)
