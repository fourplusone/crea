from toposort import toposort
from collections import namedtuple

_Functor = namedtuple("Functor", ['consumes', 'provides', 'name', 'is_pure'])
Signal = namedtuple("Signal", ['name', 'type'])


class Functor(_Functor):
    @property
    def signature(self):
        return ", ".join(['uint8 ' + consumed for consumed in self.consumes])
    
    @property
    def bindings(self):
        return ", ".join(['storageSignal_' + consumed for consumed in self.consumes])




def generate_files(functors):
    
    
    
    
    dag = {}
    signals_to_functor = {}
    data_provided = []
    
    for f in functors:
        data_provided += f.provides
        for p in f.provides:
            dag[p] = set(f.consumes)
            assert p not in signals_to_functor, 'Duplicate Signal'
            signals_to_functor[p] = f
        
        if not f.is_pure:
            dummy_signal = '__dummy' + f.name
            dag[dummy_signal] = set(f.consumes)
            signals_to_functor[dummy_signal] = f
    topolist = list(toposort(dag))

    def functor_for_signal(name):
        return signals_to_functor[name]
        
    with open("functor_header.h", 'w') as fd_header, \
        open("functor_impl_template.c", 'w') as fd_impl:
        
        fd_header.write("""
#ifndef functor_header_h
#define functor_header_h
""")
        fd_impl.write("""
#include <stdio.h>
#include "functor_header.h"
#include "functor_eval.h"

""")
        for x in functors:
            if len(x.provides) < 1 and x.is_pure: continue
        
            fd_header.write("""void evaluate_functor_{}({});
""".format(x.name, x.signature))
        
            fd_impl.write("""
void evaluate_functor_{i}({signature})
{{
    printf("evaluating functor {i} {fmt}\\n\\n"{args});
}}
""".format(i=x.name, signature=x.signature,
               fmt=', '.join(["%d " for _ in x.consumes]),
              args=', '.join([''] + ['storageSignal_'+p for p in x.consumes])))
    
        fd_header.write("""
#endif
""")


    with open("functor_eval.h", 'w') as fd_header, \
        open("functor_eval.c", 'w') as fd_impl:
    
        fd_header.write("#ifndef functor_eval_h\n#define functor_eval_h\n\n#include <stdlib.h>\n\n")
        fd_header.write("typedef enum {\n")
        for functor in functors:
            if not functor.is_pure:
                fd_header.write("    enEvent_{},\n".format(functor.name))
        fd_header.write("    enEvent_INVALID,\n")
        fd_header.write("} external_event_t;\n\n")
    
    
        fd_impl.write("""

#include <memory.h>
#include "functor_eval.h"
#include "functor_header.h"
#include "bitfield.h"


static BITFIELD_DECL(uint32_t, signal_changed, {num_changed});
static external_event_t external_event;
    """.format(num_changed=len(data_provided)))
    
        for x in signals_to_functor:
            if x in data_provided:
                fd_header.write("#define nSignal_{} {}\n".format(x, data_provided.index(x)))
                fd_header.write("extern uint8_t storageSignal_{};\n".format(x, data_provided.index(x)))
                fd_impl.write("uint8_t storageSignal_{} = 0;\n".format(x, data_provided.index(x)))
            else:
                fd_header.write("#define nSignal_{} -1\n".format(x))
                
        for i,t in enumerate(topolist):
            fd_impl.write("static void process_layer_{}(void);\n".format(i))
            fd_impl.write("static void process_layer_{}() {{\n".format(i))
        
            functors = []
            for x in t:
                functor = functor_for_signal(x)
                if functor not in functors:
                    functors.append(functor)
                
            for functor in functors:
                fd_impl.write("    if ( 0")
                dependencies = functor.consumes
                if len(dependencies) > 0:
                    for a in dependencies:
                        fd_impl.write(" || bitfield_get(signal_changed, nSignal_{})".format(a))
                if not functor.is_pure:
                    fd_impl.write(" || external_event == enEvent_{}".format(functor.name))
                
                
                fd_impl.write(') {{ \n        evaluate_functor_{functor}({bindings});\n'.format(
                functor=functor.name,
                bindings=functor.bindings) )
                for signal in functor.provides:
                    fd_impl.write('        bitfield_set(signal_changed, nSignal_{sig_name});\n'.format(sig_name=signal))
                fd_impl.write('    }\n\n')
            
            
            fd_impl.write("}\n")
    
        fd_header.write("void process_layers(external_event_t event);\n")
        fd_impl.write("""
void process_layers(external_event_t event){
    external_event = event;
    memset(signal_changed,0, sizeof(signal_changed));
""")
                  
        for i,t in enumerate(topolist):
            fd_impl.write("    process_layer_{}();\n".format(i))
        fd_impl.write("}\n")
    
    
        fd_header.write("void startup();\n")
        fd_impl.write("""
void startup(external_event_t event){
""")
        for signal in topolist[0]:
            functor = functor_for_signal(signal)
            fd_impl.write('    evaluate_functor_{functor}();\n'.format(functor=functor.name))
            fd_impl.write('    bitfield_set(signal_changed, nSignal_{sig_name});\n'.format(sig_name=signal))
        for i,t in enumerate(topolist[1:]):
            fd_impl.write("    process_layer_{}();\n".format(i+1))
        fd_impl.write("}\n")
        fd_header.write("#endif\n")

if __name__ == '__main__':
    functors = [
        Functor([], ['a'], name="a", is_pure=False),
        Functor([], ['b'], name="b", is_pure=False),
        Functor([], ['c'], name="c", is_pure=False),
        Functor([], ['tick'], name="tick", is_pure=False),
    
        Functor(['a'], ['e', 'f'], name="ef", is_pure=True),
        Functor(['a'], ['g'], name="g", is_pure=True),
        Functor(['g'], ['h'], name="h", is_pure=True),
        Functor(['h','f'], ['i'], name="i", is_pure=True),
    ]
    
    generate_files(functors)