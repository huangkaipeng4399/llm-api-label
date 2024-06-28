cluster_label() {
    input_file="../cncode_ctfidf"
    output_file="../testerr1.jsonl"
    text_key="content"
    start_idx="0"

    python main.py \
        --output_file $output_file \
        --start_idx $start_idx \
        --sleep_time 10 \
        --input_file $input_file 
}

cluster_label