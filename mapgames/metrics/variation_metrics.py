class AllVariationMetrics:
    """
    Class containing all variation metrics and writting them all in teh same file.
    """

    def __init__(self, variations_scheduler, save_path, file_name, eval_batch_size, save_stat_period):
        self.instant_file = open(f"{save_path}/variationmetrics_instant_{file_name}.csv", 'w')
        self.instant_file.write("n_eval,label,instant_nb_evo,instant_nb_improv,instant_nb_discovery,instant_mean_niche_delta_fitness,instant_mean_parent_delta_fitness,instant_mean_parent_delta_bd\n")
        self.instant_file.flush()
        self.file = open(f"{save_path}/variationmetrics_{file_name}.csv", 'w')
        self.file.write("n_eval,label,nb_evo,nb_improv,nb_discovery,mean_niche_delta_fitness,mean_parent_delta_fitness,mean_parent_delta_bd\n")
        self.file.flush()

        self.nb_evaluations = 0
        self.variation_metrics_dico = {
            "random": VariationMetrics("random", self.instant_file, self.file, eval_batch_size, save_stat_period),
            "greedy": VariationMetrics("greedy", self.instant_file, self.file, eval_batch_size, save_stat_period),
        }
        for var in [variations_scheduler.pg_variation, variations_scheduler.ga_variation]:
            if var != None:
                self.variation_metrics_dico[var.label] = VariationMetrics(var.label, self.instant_file, self.file, \
                                                                          eval_batch_size, save_stat_period)

    def update(self, nb_evals, label, added, is_new, delta_f, parent_delta_f, parent_delta_bd):
        self.variation_metrics_dico[label].update(nb_evals, added, is_new, delta_f, parent_delta_f, parent_delta_bd)

    def write(self):
        for variation_metrics in self.variation_metrics_dico.values():
            variation_metrics.write()

class VariationMetrics:
    """
    Define the metrics following the use in time of one of the variation operators.
    """

    def __init__(self, label, instant_file_name, file_name, eval_batch_size, save_stat_period):
        self.label = label
        self.instant_file = instant_file_name
        self.file = file_name
        self.eval_batch_size = eval_batch_size
        self.save_stat_period = save_stat_period
        self.average_constant = float(int(float(self.save_stat_period) / float(self.eval_batch_size)))
        self.nb_evals = 0
        self.previous_reset = 0
        self.previous_write = 0
        self.instant_reset()
        self.reset()

    def update(self, nb_evals, added, is_new, delta_f, parent_delta_f, parent_delta_bd):

        # If reach batch size, reset stats
        if nb_evals - self.previous_reset >= self.eval_batch_size:
            # If reach stat save period, write stats
            if nb_evals - self.previous_write >= self.save_stat_period:
                self.write()
                self.reset()
                self.previous_write = nb_evals
            self.instant_reset()
            self.previous_reset = nb_evals
        self.nb_evals = nb_evals

        # Update stats
        assert not(is_new and not(added)), "Inconsistency between added and is_new"
        self.instant_nb_evolved += 1
        self.nb_evolved += 1
        assert added == 0 or added == 1
        self.instant_nb_improv += added
        self.nb_improv += added
        assert is_new == 0 or is_new == 1
        self.instant_nb_discovery += is_new
        self.nb_discovery += is_new
        assert delta_f == delta_f, "delta_f is NaN"
        self.instant_delta_f += delta_f
        self.delta_f += delta_f
        assert parent_delta_f == parent_delta_f, "parent_delta_f is NaN"
        self.instant_parent_delta_f += parent_delta_f
        self.parent_delta_f += parent_delta_f
        assert parent_delta_bd == parent_delta_bd, "parent_delta_bd is NaN"
        self.instant_parent_delta_bd += parent_delta_bd
        self.parent_delta_bd += parent_delta_bd


    def _sub_write(self, file_name, nb_evolved, nb_improv, nb_discovery, delta_f, parent_delta_f, parent_delta_bd):
        file_name.write(
            "{},{},{},{},{},{},{},{}\n".format(
                self.nb_evals, 
                self.label, 
                str(nb_evolved),
                str(nb_improv), 
                str(nb_discovery), 
                str(delta_f / nb_evolved if nb_evolved != 0 else 0), 
                str(parent_delta_f / nb_evolved if nb_evolved != 0 else 0), 
                str(parent_delta_bd / nb_evolved if nb_evolved != 0 else 0)
            )
        )
        file_name.flush()

    def write(self):
        print("  -> Writting stats for", self.label, "variation")
        self._sub_write(self.instant_file, self.instant_nb_evolved, self.instant_nb_improv, \
                        self.instant_nb_discovery, self.instant_delta_f, \
                        self.instant_parent_delta_f, self.instant_parent_delta_bd)
        self._sub_write(self.file, self.nb_evolved / self.average_constant, \
                        self.nb_improv / self.average_constant, self.nb_discovery / self.average_constant, \
                        self.delta_f / self.average_constant, self.parent_delta_f / self.average_constant, \
                        self.parent_delta_bd / self.average_constant)

    def instant_reset(self):
        self.instant_nb_evolved = 0
        self.instant_nb_improv = 0
        self.instant_nb_discovery = 0
        self.instant_delta_f = 0
        self.instant_parent_delta_f = 0
        self.instant_parent_delta_bd = 0

    def reset(self):
        self.nb_evolved = 0
        self.nb_improv = 0
        self.nb_discovery = 0
        self.delta_f = 0
        self.parent_delta_f = 0
        self.parent_delta_bd = 0

