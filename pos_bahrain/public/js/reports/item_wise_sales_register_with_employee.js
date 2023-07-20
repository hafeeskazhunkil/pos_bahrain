import { load_filters_on_load } from './utils';

import { added_fields } from './sales_register_with_employee';

export default function () {
  return {
    onload: load_filters_on_load('Item-wise Sales Register', (filters) => [
      ...filters,
      ...added_fields,
    ]),
    filters: [],
  };
}
