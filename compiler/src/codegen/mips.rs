// ─────────────────────────────────────────────────────────
//  MipsBackend  —  IR-native
// ─────────────────────────────────────────────────────────
pub struct MipsBackend {
    // ... (rest of the struct remains the same)

    // Data section
    next_data:   u32,
    data_symbols: HashMap<String, u32>,
    root_vars:   std::collections::HashSet<String>,
    label_usage: HashMap<String, bool>, // new field to track label usage
}

impl MipsBackend {
    // ... (rest of the implementation remains the same)

    fn emit_module(&mut self, module: &IrModule) {
        // ... (rest of the implementation remains the same)

        // Pass 1: سجّل كل الـ MK labels الموجودة
        for (i, instr) in module.instructions.iter().enumerate() {
            if instr.op == IrOp::Mk {
                if let Some(Operand::Label(name)) = instr.operands.first() {
                    self.labels.insert(name.clone(), i);
                    self.label_usage.insert(name.clone(), true); // mark label as used
                }
            }
        }

        // Pass 2: emit
        for instr in &module.instructions {
            self.current_line += 1;
            self.emit_instr(instr);
        }

        // Pass 3: resolve forward patches
        self.resolve_patches();

        // Pass 4: resolve Rdf instructions
        for instr in &module.instructions {
            if instr.op == IrOp::Rdf {
                if let Operand::VReg(name) = &instr.operands[0] {
                    if self.label_usage.contains_key(name) {
                        // label is used, treat its immediate value as a literal address
                        if let Operand::Imm(val) = &instr.operands[1] {
                            self.data_symbols.insert(name.clone(), *val as u32);
                        }
                    } else {
                        // label is not used, allocate a fresh address
                        let addr = self.next_data;
                        self.data_symbols.insert(name.clone(), addr);
                        self.next_data += 4;
                    }
                }
            }
        }
    }

    // ... (rest of the implementation remains the same)
}