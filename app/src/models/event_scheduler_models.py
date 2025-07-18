from pydantic import BaseModel, Field, EmailStr

class ComparisonVariables(BaseModel):
    brand: str = Field(description="brand name of the product", max_length=20)
    industry: str = Field(description="industry of the product")
    year: int = Field(description="Year of the product information", ge=2000)


class ColorTrendVariables(BaseModel):
    brand: str = Field(description="brand name of the product", max_length=20)
    start_year: int = Field(description="Starting year of the product information")
    end_year: int = Field(description="Ending year of the product information")


class PrechatVariables(BaseModel):
    full_name: str = Field(description="Full name of the user", max_length=20)
    mobile_number: int = Field(
        description="Mobile Number of the user must be of 10 digits.",
        max_length=10,
        min_length=10,
    )
    email_id: str = Field(description="mail ID of the user", max_length=20)


class GetEventsSchema(BaseModel):
    start_datetime: str = Field(
        description=(
            "The start datetime for the event in the following format: "
            'YYYY-MM-DDTHH:MM:SS, where "T" separates the date and time.'
        )
    )
    end_datetime: str = Field(
        description=(
            "The end datetime for the event in the following format: "
            'YYYY-MM-DDTHH:MM:SS, where "T" separates the date and time.'
        )
    )
    agenda: str
    user_email: EmailStr

    timezone: str = Field(
        default="Asia/Kolkata",
    )