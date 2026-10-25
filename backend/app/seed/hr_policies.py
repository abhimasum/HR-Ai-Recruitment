from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.db.vector_store import add_chunks, count_chunks

SAMPLE_POLICIES: dict[str, str] = {
    "Work From Home Policy": """
Employees may work remotely up to three days per week after completing their probation period.
Remote days must be agreed with the line manager in advance. Employees must be reachable during
core hours of 10:00 to 16:00 local time. Company equipment for home offices is reimbursed up to
a fixed annual allowance. Fully remote roles are listed explicitly in the job posting.
""",
    "Paid Leave Policy": """
Full-time employees receive 20 days of paid annual leave per calendar year, accrued monthly.
Unused leave of up to 5 days may be carried over to the next year. Sick leave is 10 paid days
per year; a doctor's note is required for absences longer than 3 consecutive days. Parental leave
provides 16 weeks of fully paid leave for the primary caregiver and 4 weeks for the secondary caregiver.
""",
    "Health Insurance": """
The company provides medical, dental, and vision insurance covering employees and dependents from
the first day of employment. The company pays 90 percent of the premium for employees and 60 percent
for dependents. Annual wellness allowances can be used for gym memberships or mental health services.
Enrollment changes are allowed only during the open enrollment window in November.
""",
    "Hiring Pipeline Steps": """
The recruitment process has five stages. First, the recruiter conducts a 30-minute screening call.
Second, the candidate completes a technical or role-specific assessment. Third, there are two
interview rounds with the hiring team. Fourth, a culture conversation is held with a panel. Finally,
the offer is extended, typically within five business days of the final interview. Candidates receive
feedback after every stage.
""",
    "Diversity and Life at Company": """
The company is committed to an inclusive workplace where everyone can contribute fully. Employee
resource groups meet monthly and are open to all staff. The company hosts quarterly all-hands meetings,
a learning budget of 1,000 USD per year per employee, and team offsites twice a year. Flexible
working hours are available on request for caregivers and students.
""",
}


async def seed_policies_if_empty() -> None:
    if await count_chunks() > 0:
        return
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    for source, body in SAMPLE_POLICIES.items():
        await add_chunks(source, splitter.split_text(body.strip()))
