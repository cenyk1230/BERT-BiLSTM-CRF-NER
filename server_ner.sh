bert-base-serving-start \
    -model_dir ./output_ner \
    -bert_model_dir ./albert_tiny \
    -model_pb_dir ./output_ner_pb \
    -port 6666 \
    -port_out 6667 \
    -mode NER
