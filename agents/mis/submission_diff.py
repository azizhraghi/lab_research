"""Compare preserved research versions without treating timestamps as edits."""

def compare_snapshots(before, after):
    changes = []
    for section, keys in (
        ('dossier', ('questions', 'approach', 'findings', 'limitations')),
        ('operations', ('project', 'outstanding', 'staff', 'budgets')),
    ):
        for key in keys:
            old, new = before.get(section, {}).get(key), after.get(section, {}).get(key)
            if old != new:
                changes.append(dict(section=section, field=key, kind='changed', before=old, after=new))
    for section, keys in (
        ('dossier', ('references', 'claims', 'evaluations')),
        ('operations', ('milestones', 'deliverables', 'risks')),
    ):
        for key in keys:
            old = {str(r['id']): r for r in before.get(section, {}).get(key, [])}
            new = {str(r['id']): r for r in after.get(section, {}).get(key, [])}
            for identity in sorted(old.keys() | new.keys()):
                if old.get(identity) != new.get(identity):
                    changes.append(dict(section=section, field=key, id=identity,
                        kind='added' if identity not in old else 'removed' if identity not in new else 'changed',
                        before=old.get(identity), after=new.get(identity)))
    return changes
