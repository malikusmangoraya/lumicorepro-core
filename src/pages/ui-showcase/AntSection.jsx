import 'antd/dist/reset.css';
import { ConfigProvider, Button, Card, Tag, Space } from 'antd';

export default function AntSection() {
  return (
    <ConfigProvider>
      <Card title="Ant Design (antd v6)" style={{ maxWidth: 520 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Space>
            <Button type="primary">Primary</Button>
            <Button>Default</Button>
            <Button type="dashed">Dashed</Button>
            <Button type="text">Text</Button>
          </Space>
          <Space>
            <Tag color="blue">blue</Tag>
            <Tag color="green">green</Tag>
            <Tag color="orange">orange</Tag>
          </Space>
        </Space>
      </Card>
    </ConfigProvider>
  );
}
