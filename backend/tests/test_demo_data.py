from app.demo.data import TEAMS


def test_authored_cases_have_distinct_people_and_work_examples():
    people = [person for team in TEAMS for person in team.people]
    assert len(people) == 60
    for field in ("name", "task", "evidence", "development"):
        assert len({getattr(person, field) for person in people}) == len(people)
    assert all(len(team.people) == 10 for team in TEAMS)
    assert all(team.people[0].position == "Naczelnik wydziału" for team in TEAMS)
    assert all(len(person.evidence) > 100 for person in people)
    assert len({team.slug for team in TEAMS}) == len(TEAMS)
