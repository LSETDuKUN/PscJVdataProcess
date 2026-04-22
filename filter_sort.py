def filter_files(files, min_pce=0, min_voc=0, min_jsc=0, min_ff=0, logic="AND"):
    effective = []
    uneffective = []
    for f in files:
        cond_pce = (f.PCE is not None and f.PCE >= min_pce)
        cond_voc = (f.Voc is not None and f.Voc >= min_voc)
        cond_jsc = (f.Jsc is not None and f.Jsc >= min_jsc)
        cond_ff = (f.FF is not None and f.FF >= min_ff)

        if logic == "AND":
            met = cond_pce and cond_voc and cond_jsc and cond_ff
        else:
            met = cond_pce or cond_voc or cond_jsc or cond_ff

        if met:
            effective.append(f)
        else:
            uneffective.append(f)
    return effective, uneffective


def sort_files(files, key="PCE", reverse=True):
    return sorted(files, key=lambda x: getattr(x, key) or 0, reverse=reverse)