// ─────────────────────────────────────────────────────────
//  MipsBackend  —  IR-native
// ─────────────────────────────────────────────────────────
pub struct MipsBackend {
    // ... (rest of the struct remains the same)

    // Data section
    next_data:   u32,
    data_symbols: HashMap<String, u32>,
    root_vars:   std::collections::HashSet<String>,
    label_usage: std::collections::HashSet<String>, // New field to track label usage
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
                    self.label_usage.insert(name.clone()); // Mark label as used
                }
            }
        }

        // ... (rest of the implementation remains the same)

        // Pass 2: emit
        for instr in &module.instructions {
            self.current_line += 1;
            self.emit_instr(instr);
        }

        // ... (rest of the implementation remains the same)

        // Pass 3: resolve forward patches
        self.resolve_patches();
    }

    fn emit_instr(&mut self, instr: &crate::ir::IrInstr) {
        match &instr.op {
            // ... (rest of the implementation remains the same)

            // ── Rdf @name; imm ─────────────────────────────
            IrOp::Rdf => {
                if instr.operands.len() < 2 { return; }
                if let Operand::VReg(name) = &instr.operands[0] {
                    self.root_vars.insert(name.clone());
                    if let Operand::Imm(val) = &instr.operands[1] {
                        // Check if the label is used elsewhere
                        if self.label_usage.contains(name) {
                            // If used as a label, store the immediate value as a literal address
                            self.data_symbols.insert(name.clone(), *val as u32);
                        } else {
                            // If not used as a label, allocate a fresh address from next_data
                            let addr = self.next_data;
                            self.data_symbols.insert(name.clone(), addr);
                            self.next_data += 4;
                        }
                    } else {
                        // If the operand is not an immediate, allocate a fresh address from next_data
                        let addr = self.next_data;
                        self.data_symbols.insert(name.clone(), addr);
                        self.next_data += 4;
                    }
                }
            }

            // ... (rest of the implementation remains the same)
        }
    }
}