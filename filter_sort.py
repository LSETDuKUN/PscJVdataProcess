def filter_files(files, min_pce=0, min_voc=0, min_jsc=0, min_ff=0, logic=("AND", "AND", "AND")):
    effective = []
    uneffective = []
    for f in files:
        cond_pce = (f.PCE is not None and f.PCE >= min_pce)
        cond_voc = (f.Voc is not None and f.Voc >= min_voc)
        cond_jsc = (f.Jsc is not None and f.Jsc >= min_jsc)
        cond_ff = (f.FF is not None and f.FF >= min_ff)

        # evaluate sequentially from left to right: (((PCE op1 Voc) op2 Jsc) op3 FF)
        met = cond_pce
        if logic[0] == "AND": met = met and cond_voc
        else: met = met or cond_voc

        if logic[1] == "AND": met = met and cond_jsc
        else: met = met or cond_jsc

        if logic[2] == "AND": met = met and cond_ff
        else: met = met or cond_ff

        if met:
            effective.append(f)
        else:
            uneffective.append(f)
    return effective, uneffective


def sort_files(files, key="PCE", reverse=True):
    return sorted(files, key=lambda x: getattr(x, key) or 0, reverse=reverse)