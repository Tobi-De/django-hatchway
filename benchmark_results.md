# Benchmark Results

## Metadata

- **framework**: django-hatchway
- **python_version**: 3.14.2 (main, Dec  9 2025, 19:03:28) [Clang 21.1.4 ]

## Results

| Name | Min (µs) | Max (µs) | Mean (µs) | Median (µs) | StdDev | OPS |
|------|----------|----------|-----------|-------------|--------|-----|
| test_post_list_empty | 263.36 | 590.65 | 305.96 | 298.95 | 33.24 | 3268 |
| test_post_list_small | 4217.89 | 6574.76 | 4592.51 | 4565.00 | 250.88 | 218 |
| test_post_list_medium | 4442.74 | 6674.34 | 4779.93 | 4721.46 | 252.91 | 209 |
| test_post_list_large | 4679.28 | 5429.21 | 4959.55 | 4938.87 | 140.68 | 202 |
| test_post_list_with_filters | 8309.01 | 9172.07 | 8666.87 | 8605.43 | 204.03 | 115 |
| test_post_detail | 779.77 | 1163.34 | 861.04 | 852.12 | 54.36 | 1161 |
| test_post_detail_with_many_comments | 775.95 | 1132.66 | 858.31 | 846.56 | 59.01 | 1165 |
| test_post_create_simple | 738.87 | 1104.37 | 811.07 | 802.39 | 46.08 | 1233 |
| test_post_create_large_content | 809.79 | 1189.04 | 893.81 | 882.51 | 53.63 | 1119 |
| test_post_search_small | 526.35 | 832.73 | 591.75 | 584.36 | 42.11 | 1690 |
| test_post_search_large | 1093.78 | 1560.18 | 1204.70 | 1187.50 | 73.08 | 830 |
| test_bulk_create_10 | 1769.79 | 2353.72 | 1944.63 | 1926.95 | 110.81 | 514 |
| test_bulk_create_50 | 8592.15 | 16600.59 | 9156.69 | 8997.62 | 868.23 | 109 |
| test_post_comments_list | 1037.18 | 2758.76 | 1206.29 | 1142.31 | 237.82 | 829 |
| test_comment_create | 643.81 | 914.27 | 711.12 | 700.29 | 46.63 | 1406 |
| test_simple_schema | 321.35 | 937.13 | 371.77 | 363.45 | 42.85 | 2690 |
| test_complex_schema | 327.00 | 562.45 | 371.46 | 364.31 | 30.76 | 2692 |
| test_list_serialization | 17667.45 | 18946.17 | 18196.40 | 18150.29 | 268.22 | 55 |
| test_full_stack_overhead | 785.47 | 1275.09 | 871.46 | 860.88 | 60.94 | 1147 |
| test_schema_response | 7980.75 | 9291.05 | 8382.93 | 8356.48 | 200.71 | 119 |
| test_simple_query_params | 15.34 | 63.13 | 17.66 | 17.44 | 1.58 | 56623 |
| test_complex_query_params | 17.04 | 51.91 | 19.43 | 19.24 | 1.45 | 51471 |
| test_body_validation | 16.91 | 50.96 | 19.55 | 19.42 | 1.40 | 51151 |
| test_mixed_sources | 18.76 | 52.52 | 21.29 | 21.05 | 1.59 | 46968 |
| test_sources_for_input | 6.31 | 39.10 | 6.85 | 6.78 | 0.67 | 145936 |
| test_extract_signifier | 3.33 | 36.00 | 3.61 | 3.58 | 0.35 | 276932 |
| test_is_optional | 1.62 | 27.63 | 1.82 | 1.81 | 0.23 | 549069 |
| test_minimal_view_overhead | 11.57 | 91.43 | 13.48 | 13.35 | 1.52 | 74198 |
| test_no_validation_overhead | 12.99 | 46.29 | 15.28 | 15.09 | 1.40 | 65454 |
| test_validation_success | 16.02 | 57.62 | 18.81 | 18.65 | 1.57 | 53171 |
| test_validation_failure | 18.21 | 68.37 | 20.68 | 20.49 | 1.62 | 48366 |
| test_dict_response | 14.48 | 57.94 | 16.48 | 16.31 | 1.41 | 60668 |
| test_list_response | 86.52 | 142.71 | 91.66 | 90.01 | 4.94 | 10910 |
