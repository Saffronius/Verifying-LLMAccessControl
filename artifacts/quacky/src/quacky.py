from frontend import validate_args
# from tabulate import tabulate
from translator import call_translator
from utilities import *
from utils.Shell import Shell

import argparse as ap
import math
import os

def call_abc(args):
    shell = Shell()
    policy1, policy2 = validate_args(args)

    # Call ABC on formula 1
    cmd = 'abc -bs {} -v 0 -i {}_1.smt2 --precise --count-tuple'.format(args.bound, args.output)
    if args.variable:
        cmd += ' --count-variable principal,action,resource'

    if args.models and int(args.models) > 0:
        filename = os.path.abspath(os.getcwd())+"/P1_not_P2.models"
        with open(filename,"w") as f:
            pass
        cmd += ' --get-num-random-models {} {} {} resource {}'.format(args.models, args.minrange, args.maxrange, filename)
    
    if args.printregex:
        cmd += ' --print-regex resource'

    out, err = shell.runcmd(cmd)
    if args.verbose:
        print(out, err)

    result1 = get_abc_result_line(out, err)

    print('Policy 1 ⇏ Policy 2' if policy2 else 'Policy 1')

    # Format results table
    # table1 = [
    #     ['Solve Time (ms)', result1['solve_time']],
    #     ['satisfiability', result1['is_sat']]
    # ]

    print("Solve Time (ms): " + result1['solve_time'])
    print("satisfiability: " + result1['is_sat'])

    if 'count' in result1 and int(result1['count']) > 0:
        print("Count Time (ms): " + result1['count_time'])
        print("lg(requests): " + str(math.log2(int(result1['count']))))
        # table1 += [
        #     ['Count Time (ms)', result1['count_time']],
        #     ['lg(requests)', math.log2(int(result1['count']))]
        # ]
    else:
        print("requests: 0")
        # table1.append(['requests', 0])

    # for k, v in result1['var'].items():
    #     if int(v['count']) > 0:
    #         table1.append(['lg({})'.format(k), math.log2(int(v['count']))])
    #     else:
    #         table1.append([k, 0])
    
    
    # print(tabulate(table1, tablefmt = 'fancy_grid'))
    print()

    if args.printregex and 'count' in result1:
        print("regex_from_dfa: {}".format(result1['regex_from_dfa']))

    # if given regex for resource, compare against resources from policy comparison
    if args.compareregex:
        cmd = 'abc -bs {} -v 0 -i {}_1.smt2 --precise --count-tuple'.format(args.bound, args.output)
        cmd += ' --compare-regex {} {}'.format('resource', args.compareregex)
        # print(cmd)
        out, err = shell.runcmd(cmd)
        if args.verbose:
            print(out, err)

        result = get_abc_result_line(out, err)
        is_valid = ('is_sat' in result and result['is_sat'] == 'sat')
        print(result)
        if is_valid and "baseline_regex" not in result:
            error = ""
            error += "FATAL ERROR FROM ABC" + '\n'
            error += "------output from ABC:-----" + '\n'
            error += out + '\n'
            error += "------error from ABC:-----" + '\n'
            error += err + '\n'
            error += "------output_1.smt2:-----" + '\n'
            with open("{}_1.smt2".format(args.output),'r') as f:
                error += f.read() + '\n'
            error += "------output_2.smt2:-----" + '\n'
            with open("{}_2.smt2".format(args.output),'r') as f:
                error += f.read() + '\n'
            error += "------regex from input-----" + '\n'
            with open(args.compareregex, 'r') as f:
                error += f.read() + '\n'
            error += "------policy1----" + '\n'
            with open(args.policy1, 'r') as f:
                error += f.read() + '\n'
            error += "-----policy2----" + '\n'
            if args.policy2:
                with open(args.policy2, 'r') as f:
                    error += f.read() + '\n'
            error += "FATAL END"
            
            raise Exception(error)

        print("-----------------------------------------------------------")
        print("Baseline Regex Count          : " + (result["baseline_regex"] if is_valid else '0'))
        print("Synthesized Regex Count       : " + (result["synthesized_regex"] if is_valid else '0'))
        print("Baseline_Not_Synthesized Count: " + (result["baseline_not_synthesized"] if is_valid else '0'))
        print("Not_Baseline_Synthesized_Count: " + (result["not_baseline_synthesized"] if is_valid else '0'))
        print("regex_from_dfa                : " + (result["regex_from_dfa"] if is_valid else '0'))
        print("regex_from_llm                : " + (result["regex_from_llm"] if is_valid else '0'))
        print("ops_regex_from_dfa            : " + (result["ops_regex_from_dfa"] if is_valid else '0'))
        print("ops_regex_from_llm            : " + (result["ops_regex_from_llm"] if is_valid else '0'))
        print("length_regex_from_dfa         : " + (result["length_regex_from_dfa"] if is_valid else '0'))
        print("length_regex_from_llm         : " + (result["length_regex_from_llm"] if is_valid else '0'))
        print("jaccard_numerator             : " + (result["jaccard_numerator"] if is_valid else '0'))
        print("jaccard_denominator           : " + (result["jaccard_denominator"] if is_valid else '0'))
        print("similarity1                   : " + (str(round(int(result["jaccard_numerator"]) / int(result["jaccard_denominator"]),2)) if is_valid else '0'))
        
        
    if not policy2:
        return

    # Call ABC on formula 2
    cmd = 'abc -bs {} -v 0 -i {}_2.smt2 --precise --count-tuple'.format(args.bound, args.output)
    if args.variable:
        cmd += ' --count-variable principal,action,resource'
        
    if args.models and int(args.models) > 0:
        filename = os.path.abspath(os.getcwd())+"/not_P1_P2.models"
        with open(filename,"w") as f:
            pass
        cmd += ' --get-num-random-models {} {} {} resource {}'.format(args.models, args.minrange, args.maxrange, filename)
    
    out, err = shell.runcmd(cmd)
    if args.verbose:
        print(out, err)

    result2 = get_abc_result_line(out, err)
    
    print('Policy 2 ⇏ Policy 1')
    print("Solve Time (ms): " + result2['solve_time'])
    print("satisfiability: " + result2['is_sat'])

    # Format results table
    # table2 = [
    #     ['Solve Time (ms)', result2['solve_time']],
    #     ['satisfiability', result2['is_sat']]
    # ]

    if 'count' in result2 and int(result2['count']) > 0:
        print("Count Time (ms): " + result2['count_time'])
        print("lg(requests): " + str(math.log2(int(result2['count']))))
        # table2 += [
        #     ['Count Time (ms)', result2['count_time']], 
        #     ['lg(requests)', math.log2(int(result2['count']))]
        # ]
    else:
        print("requests: 0")
        # table2.append(['requests', 0])

    # for k, v in result2['var'].items():
    #     if int(v['count']) > 0:
    #         table2.append(['lg({})'.format(k), math.log2(int(v['count']))])
    #     else:
    #         table2.append([k, 0])
    
    # print('Policy 2 ⇏ Policy 1')
    # print(tabulate(table2, tablefmt = 'fancy_grid'))
    print()

    # if given regex for resource, compare against resources from policy comparison
    if args.compareregex:
        cmd = 'abc -bs {} -v 0 -i {}_2.smt2 --precise --count-tuple'.format(args.bound, args.output)
        cmd += ' --compare-regex {} {}'.format('resource', args.compareregex2)
        out, err = shell.runcmd(cmd)
        if args.verbose:
            print(out, err)

        result = get_abc_result_line(out, err)
        is_valid = ('is_sat' in result and result['is_sat'] == 'sat')
        if is_valid and "baseline_regex" not in result:
            error = ""
            error += "FATAL ERROR FROM ABC" + '\n'
            error += "------output from ABC:-----" + '\n'
            error += out + '\n'
            error += "------error from ABC:-----" + '\n'
            error += err + '\n'
            error += "------output_1.smt2:-----" + '\n'
            with open("{}_1.smt2".format(args.output),'r') as f:
                error += f.read() + '\n'
            error += "------output_2.smt2:-----" + '\n'
            with open("{}_2.smt2".format(args.output),'r') as f:
                error += f.read() + '\n'
            error += "------regex2 from input-----" + '\n'
            with open(args.compareregex2, 'r') as f:
                error += f.read() + '\n'
            error += "------policy1----" + '\n'
            with open(args.policy1, 'r') as f:
                error += f.read() + '\n'
            error += "-----policy2----" + '\n'
            if args.policy2:
                with open(args.policy2, 'r') as f:
                    error += f.read() + '\n'
            error += "FATAL END"
            
            raise Exception(error)

        print("-----------------------------------------------------------")
        print("Baseline Regex Count          : " + (result["baseline_regex"] if is_valid else '0'))
        print("Synthesized Regex Count       : " + (result["synthesized_regex"] if is_valid else '0'))
        print("Baseline_Not_Synthesized Count: " + (result["baseline_not_synthesized"] if is_valid else '0'))
        print("Not_Baseline_Synthesized_Count: " + (result["not_baseline_synthesized"] if is_valid else '0'))
        print("regex_from_dfa                : " + (result["regex_from_dfa"] if is_valid else '0'))
        print("regex_from_llm                : " + (result["regex_from_llm"] if is_valid else '0'))
        print("ops_regex_from_dfa            : " + (result["ops_regex_from_dfa"] if is_valid else '0'))
        print("ops_regex_from_llm            : " + (result["ops_regex_from_llm"] if is_valid else '0'))
        print("length_regex_from_dfa         : " + (result["length_regex_from_dfa"] if is_valid else '0'))
        print("length_regex_from_llm         : " + (result["length_regex_from_llm"] if is_valid else '0'))
        print("jaccard_numerator             : " + (result["jaccard_numerator"] if is_valid else '0'))
        print("jaccard_denominator           : " + (result["jaccard_denominator"] if is_valid else '0'))
        print("similarity2                   : " + (str(round(int(result["jaccard_numerator"]) / int(result["jaccard_denominator"]),2)) if is_valid else '0'))
        print()



    if result1['is_sat'] == 'sat' and result2['is_sat'] == 'sat':
        print('Policy 1 and Policy 2 do not subsume each other.')
    elif result1['is_sat'] == 'sat' and result2['is_sat'] == 'unsat':
        print('Policy 1 is more permissive than Policy 2.')
    elif result1['is_sat'] == 'unsat' and result2['is_sat'] == 'sat':
        print('Policy 1 is less permissive than Policy 2.')
    else:
        print('Policy 1 and Policy 2 are equivalent.')

if __name__ == '__main__':
    parser = ap.ArgumentParser(description = 'Quantitatively analyze permissiveness of access control policies')
    parser.add_argument('-p1' , '--policy1'         , help = 'policy 1 (AWS)'               , required = False)
    parser.add_argument('-p2' , '--policy2'         , help = 'policy 2 (AWS)'               , required = False)
    parser.add_argument('-rd' , '--role-definitions', help = 'role definitions (Azure)'     , required = False)
    parser.add_argument('-ra1', '--role-assignment1', help = 'role assignment 1 (Azure)'    , required = False)
    parser.add_argument('-ra2', '--role-assignment2', help = 'role assignment 2 (Azure)'    , required = False)
    parser.add_argument('-r'  , '--roles'           , help = 'roles (GCP)'                  , required = False)
    parser.add_argument('-rb1', '--role-binding1'   , help = 'role binding 1 (GCP)'         , required = False)
    parser.add_argument('-rb2', '--role-binding2'   , help = 'role binding 2 (GCP)'         , required = False)
    # parser.add_argument('-d'  , '--domain'          , help = 'domain file (not supported)'  , required = False)
    parser.add_argument('-o'  , '--output'          , help = 'output file'                  , required = False, default = 'output')
    parser.add_argument('-s'  , '--smt-lib'         , help = 'use SMT-LIB syntax'           , required = False, action = 'store_true')
    parser.add_argument('-e'  , '--enc'             , help = 'use action encoding'          , required = False, action = 'store_true')
    parser.add_argument('-c'  , '--constraints'     , help = 'use resource type constraints', required = False, action = 'store_true')
    parser.add_argument('-b'  , '--bound'           , help = 'bound'                        , required = True , default = 100)
    parser.add_argument('-f'  , '--variable'        , help = 'count all variables'          , required = False, action = 'store_true')
    parser.add_argument('-m'  , '--models'          , help = 'get random number of models'  , required = False)
    parser.add_argument('-m1' , '--minrange'       , help = 'min length of models'         , required = False, default = 0)
    parser.add_argument('-m2' , '--maxrange'       , help = 'max length of models'         , required = False, default = 0)
    parser.add_argument('-pr' , '--printregex'   , help = 'print regex extracted from dfa', required = False, action = 'store_true')
    parser.add_argument('-cr' , '--compareregex'   , help = 'compare given regex resource during policy comparison', required = False)
    parser.add_argument('-cr2' , '--compareregex2'   , help = 'compare given regex resource during policy comparison', required = False)
    parser.add_argument('-v', '--verbose', help = 'Verbose', required = False, action = 'store_true')


    args = parser.parse_args()

    call_translator(args)
    call_abc(args)
